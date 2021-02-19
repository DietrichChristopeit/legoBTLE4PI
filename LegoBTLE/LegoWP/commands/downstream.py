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
from LegoBTLE.LegoWP.types import (COMMAND_STATUS, CONNECTION_TYPE, EVENT, HUB_ACTION, HUB_ALERT, HUB_ALERT_OPERATION,
                                   M_TYPE)


@dataclass
class HUB_ACTION_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_HUB_ACTION)
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + bytearray(self.hub_action)
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND
    
    def __len__(self) -> int:
        return int.from_bytes(self.length, 'little', signed=False)


@dataclass
class HUB_ALERT_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_DNS_HUB_ALERT)
    hub_alert: bytes = field(init=True, default=HUB_ALERT.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND
    
    def __len__(self) -> int:
        return len(self.COMMAND)


@dataclass
class PORT_NOTIFICATION_REQ:
    
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_NOTIFICATION)
    port: bytes = field(init=True, default=b'\x00')
    hub_action: bytes = field(init=True, default=M_TYPE.UPS_DNS_HUB_ACTION)
    delta_interval: bytes = field(init=True, default=b'\x01\x00\x00\x00')
    notif_enabled: bytes = field(init=True, default=COMMAND_STATUS.ENABLED)

    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.port) + \
                       bytearray(self.hub_action) + \
                       bytearray(self.delta_interval) + \
                       bytearray(self.notif_enabled)
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND

    # b'\x0a\x00\x41\x00\x02\x01\x00\x00\x00\x01'


@dataclass
class PORT_CMD_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    

@dataclass
class VIRTUAL_PORT_SETUP:
    
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_VIRTUAL_PORT_SETUP)
    status: bytes = field(init=True, default=CONNECTION_TYPE.CONNECT)
    v_port: bytes = None
    port_a: bytes = None
    port_b: bytes = None
    
    def __post_init__(self):
        
        if self.status == CONNECTION_TYPE.CONNECT:
            self.COMMAND = self.header.COMMAND + \
                self.status + \
                self.port_a + \
                self.port_b
        elif self.status == CONNECTION_TYPE.DISCONNECT:
            self.COMMAND = self.header.COMMAND + \
                           self.status + \
                           self.v_port
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND


@dataclass
class GENERAL_PORT_NOTIFICATEION_REQ:
    COMMAND = b'\x01\x00'
