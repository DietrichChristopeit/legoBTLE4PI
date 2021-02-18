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
from dataclasses import dataclass

# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE

@dataclass
class HUB_ACTION:
    DNS_HUB_SWITCH_OFF: bytes = b'\x01'
    DNS_HUB_DISCONNECT: bytes = b'\x02'
    DNS_HUB_VCC_PORT_CTRL_ON: bytes = b'\x03'
    DNS_HUB_VCC_PORT_CTRL_OFF: bytes = b'\x04'
    DNS_HUB_INDICATE_BUSY_ON: bytes = b'\x05'
    DNS_HUB_INDICATE_BUSY_OFF: bytes = b'\x06'
    DNS_HUB_FAST_SHUTDOWN: bytes = b'\x2F'
    
    UPS_HUB_WILL_SWITCH_OFF: bytes = b'\x30'
    UPS_HUB_WILL_DISCONNECT: bytes = b'\x31'
    UPS_HUB_WILL_BOOT: bytes = b'\x32'
    
    def __len__(self) -> int:
        return 1
