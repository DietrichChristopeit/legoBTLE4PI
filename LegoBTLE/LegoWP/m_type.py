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


@dataclass
class M_TYPE:
    UPS_DNS_GENERAL_HUB_NOTIFICATIONS: bytes = b'\x01'
    UPS_DNS_HUB_ACTION: bytes = b'\x02'
    UPS_DNS_DNS_HUB_ALERT: bytes = b'\x03'
    UPS_HUB_ATTACHED_IO: bytes = b'\x04'
    UPS_HUB_GENERIC_ERROR: bytes = b'\x05'
    DNS_VIRTUAL_PORT_SETUP: bytes = b'\x61'
    DNS_PORT_COMMAND: bytes = b'\x81'
    UPS_COMMAND_STATUS: bytes = b'\x82'
    UPS_PORT_VALUE: bytes = b'\x45'
    DNS_PORT_NOTIFICATION: bytes = b'\x41'
    UPS_PORT_NOTIFICATION: bytes = b'\x47'
    UPS_EXT_SERVER_ACTION: bytes = b'\x00'

    def __len__(self):
        return 1
