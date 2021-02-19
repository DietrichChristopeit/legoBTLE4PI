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

from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import COMMAND_STATUS, EVENT, HUB_ACTION, HUB_ALERT, HUB_ALERT_OPERATION, M_TYPE


@dataclass
class HUB_ACTION_SND:
    m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_HUB_ACTION)
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)
    
    def __post_init__(self):
        self.COMMAND = self.m_header.COMMAND + bytearray(self.hub_action)
        self.m_length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.m_length) + self.COMMAND
    
    def __len__(self) -> int:
        return int.from_bytes(self.m_length, 'little', signed=False)


@dataclass
class HUB_ALERT_SND:
    m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_DNS_HUB_ALERT)
    hub_alert: bytes = field(init=True, default=HUB_ALERT.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
    
    def __post_init__(self):
        self.COMMAND = self.m_header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.m_length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.m_length) + self.COMMAND
    
    def __len__(self) -> int:
        return len(self.COMMAND)


@dataclass
class PORT_NOTIFICATION_REQ:
    
    m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_NOTIFICATION)
    m_port: bytes = field(init=True, default=b'\x00')
    m_hub_action: bytes = field(init=True, default=M_TYPE.UPS_DNS_HUB_ACTION)
    m_event: bytes = field(init=True, default=EVENT.IO_ATTACHED)
    m_delta_interval: bytes = field(init=True, default=b'\x00\x00\x00')
    m_notif_enabled: bytes = field(init=True, default=COMMAND_STATUS.ENABLED)

    def __post_init__(self):
        self.COMMAND = self.m_header.COMMAND + \
                       bytearray(self.m_port) + \
                       bytearray(self.m_hub_action) + \
                       bytearray(self.m_event) + \
                       bytearray(self.m_delta_interval) + \
                       bytearray(self.m_notif_enabled)
        self.m_length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.m_length) + self.COMMAND

    # b'\x0a\x00\x41\x00\x02\x01\x00\x00\x00\x01'
    

