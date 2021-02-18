# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE

from dataclasses import dataclass, field

import LegoBTLE
from LegoBTLE.LegoWP import types
from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import CMD_FEEDBACK, COMMAND_CODES, D_TYPE, EVENT, M_TYPE


def key_name(cls, value: bytes):
    return LegoBTLE.LegoWP.types.key_name(cls.__class__, value)


@dataclass
class HUB_ACTION_RCV:
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_HUB_ACTION)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_return: bytes = self.COMMAND[self.COMMAND[0] - 1].to_bytes(1, 'little', signed=False)


@dataclass
class HUB_ATTACHED_IO_RCV:
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_HUB_ATTACHED_IO)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_port: bytes = self.COMMAND[3].to_bytes(1, 'little', signed=False)
        self.m_event: bytes = self.COMMAND[4].to_bytes(1, 'little', signed=False)
        if self.m_event in [EVENT.IO_ATTACHED, EVENT.VIRTUAL_IO_ATTACHED]:
            self.m_device_type = bytearray.fromhex(self.COMMAND[5:6].hex().zfill(4))
            self.m_device_type_str = types.key_name(D_TYPE, self.m_device_type)
            if self.m_event == EVENT.VIRTUAL_IO_ATTACHED:
                self.m_vport_a: bytes = self.COMMAND[7].to_bytes(1, 'little', signed=False)
                self.m_vport_b: bytes = self.COMMAND[8].to_bytes(1, 'little', signed=False)


@dataclass
class EXT_SERVER_RCV:
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_EXT_SERVER_CMD)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_port: bytes = self.COMMAND[3].to_bytes(1, 'little', signed=False)
        self.m_event: bytes = self.COMMAND[4].to_bytes(1, 'little', signed=False)
        self.m_event_str: str = types.key_name(EVENT, self.m_event)


@dataclass
class HUB_GENERIC_ERROR_RCV:
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_HUB_GENERIC_ERROR)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_error_cmd: bytes = self.COMMAND[3].to_bytes(1, 'little', signed=False)
        self.m_error_cmd_str: str = types.key_name(M_TYPE, self.m_error_cmd)
        self.m_error_code: bytes = self.COMMAND[4].to_bytes(1, 'little', signed=False)
        self.m_error_code_str: str = types.key_name(COMMAND_CODES, self.m_error_code)


@dataclass
class HUB_CMD_STATUS:
    COMMAND: bytearray = field(init=True)
    
    def get_status_str(self, msg) -> str:
        m_cmd_feedback = CMD_FEEDBACK()
        m_cmd_feedback.asbyte = msg
        return ((m_cmd_feedback.MSG.IDLE and 'IDLE')
                or (m_cmd_feedback.MSG.CURRENT_CMD_DISCARDED and 'CURRENT_CMD_DISCARDED ')
                or (m_cmd_feedback.MSG.EMPTY_BUF_CMD_COMPLETED and 'EMPTY_BUF_CMD_COMPLETED')
                or (m_cmd_feedback.MSG.EMPTY_BUF_CMD_IN_PROGRESS and 'EMPTY_BUF_CMD_IN_PROGRESS')
                or (m_cmd_feedback.MSG.BUSY and 'BUSY'))
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_HUB_GENERIC_ERROR)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_port = [self.COMMAND[3].to_bytes(1, 'little', signed=False)]
        self.m_cmd_status = [(self.COMMAND[4])]
        self.m_cmd_status_str = [(self.get_status_str(self.COMMAND[4]))]
        if self.m_length == b'\x07':
            self.m_cmd_status.append(self.COMMAND[6])
            self.m_port.append(self.COMMAND[5])
            self.m_cmd_status_str.append((self.get_status_str(self.COMMAND[6])))
        if self.m_length == b'\x09':
            self.m_cmd_status.append(self.COMMAND[8])
            self.m_port.append(self.COMMAND[7])
            self.m_cmd_status_str.append((self.get_status_str(self.COMMAND[8])))


@dataclass
class HUB_PORT_VALUE:
    COMMAND: bytearray = field(init=True)

    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_PORT_VALUE)
        self.m_length: bytes = self.COMMAND[0].to_bytes(1, 'little', signed=False)
        self.m_return: bytes = self.COMMAND[self.COMMAND[0] - 1].to_bytes(1, 'little', signed=False)
