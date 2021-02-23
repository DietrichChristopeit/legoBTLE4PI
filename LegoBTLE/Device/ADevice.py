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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
from abc import ABC, abstractmethod

from LegoBTLE.LegoWP.messages.downstream import CMD_EXT_SRV_CONNECT_REQ, DOWNSTREAM_MESSAGE
from LegoBTLE.LegoWP.messages.upstream import DEV_GENERIC_ERROR, HUB_ACTION, HUB_ATTACHED_IO


class Device(ABC):
    
    @property
    @abstractmethod
    def DEV_NAME(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def DEV_PORT(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def DEV_PORT_connected(self) -> bool:
        raise NotImplementedError

    @DEV_PORT_connected.setter
    @abstractmethod
    def DEV_PORT_connected(self, connected: bool):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def generic_error(self) -> DEV_GENERIC_ERROR:
        raise NotImplementedError
    
    @generic_error.setter
    @abstractmethod
    def generic_error(self, error: DEV_GENERIC_ERROR):
        raise NotImplementedError

    @property
    @abstractmethod
    def hub_action(self) -> HUB_ACTION:
        raise NotImplementedError

    @hub_action.setter
    @abstractmethod
    def hub_action(self, action: HUB_ACTION):
        raise NotImplementedError

    @property
    @abstractmethod
    def hub_attached_io(self) -> HUB_ATTACHED_IO:
        raise NotImplementedError

    @hub_attached_io.setter
    @abstractmethod
    def hub_attached_io(self, io: HUB_ATTACHED_IO):
        raise NotImplementedError

    def EXT_SRV_CONNECT_REQ(self) -> DOWNSTREAM_MESSAGE:
        return CMD_EXT_SRV_CONNECT_REQ(port=self.DEV_PORT)
    
    
        
    

