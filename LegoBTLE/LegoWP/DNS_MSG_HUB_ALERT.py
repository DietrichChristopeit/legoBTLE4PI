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
from LegoBTLE.LegoWP.hub_alert import HUB_ALERT, HUB_ALERT_OPERATION
from LegoBTLE.LegoWP.m_type import M_TYPE


@dataclass
class DNS_MSG_HUB_ALERT:
    m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_DNS_HUB_ALERT)
    hub_alert: bytes = field(init=True, default=HUB_ALERT.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
    
    def __post_init__(self):
        self.COMMAND = int.to_bytes(1 + len(self.m_header.COMMAND), 1, 'little', signed=False) + \
                       self.m_header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.m_length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.m_length) + self.COMMAND
    
    def __len__(self) -> int:
        return 1 + len(self.COMMAND)
