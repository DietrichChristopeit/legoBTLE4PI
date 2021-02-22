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
from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.messages.upstream import DEV_GENERIC_ERROR, HUB_ACTION, HUB_ATTACHED_IO


class Hub(Device):
    
    def __init__(self, name: str = 'LegoTechnicHub'):
        self._DEV_NAME = name
        self._DEV_PORT: bytes = b'\xff'
        self._last_error = None
        self._hub_action = None
        self._hub_attached_io = None
        return
    
    @property
    def DEV_NAME(self) -> str:
        return self._DEV_NAME
    
    @property
    def DEV_PORT(self) -> bytes:
        return self._DEV_PORT
    
    @property
    def generic_error(self) -> DEV_GENERIC_ERROR:
        return self._last_error
    
    @property
    def hub_action(self) -> HUB_ACTION:
        return self._hub_action
    
    @property
    def hub_attached_io(self) -> HUB_ATTACHED_IO:
        return self._hub_attached_io
