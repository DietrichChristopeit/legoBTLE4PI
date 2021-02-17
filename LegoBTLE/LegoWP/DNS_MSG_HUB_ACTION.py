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

from dataclasses import dataclass, field
# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE
from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.hub_action_type import HUB_ACTION_TYPE
from LegoBTLE.LegoWP.m_type import M_TYPE


@dataclass()
class DNS_MSG_HUB_ACTION:
    
    m_length: bytes = field(repr=True, init=False)
    m_header: bytes = field(repr=True, init=True, default=COMMON_MESSAGE_HEADER(M_TYPE.UPS_DNS_HUB_ACTION).getMessage())
    hub_action_type: bytes = field(repr=True, init=True, default=HUB_ACTION_TYPE.HUB_INDICATE_BUSY_ON)
    
    def __post_init__(self):
        self.m_length: bytes = (1 + len(self.m_header) + len(self.hub_action_type)).to_bytes(1, 'little', signed=False)
    
    def getMessage(self) -> bytearray:
        return bytearray(self.m_length + self.m_header + self.hub_action_type)
