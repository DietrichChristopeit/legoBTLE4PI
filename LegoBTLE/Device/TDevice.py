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
from abc import ABC, abstractmethod
from threading import Event


class Device(ABC):
    
    @property
    @abstractmethod
    def E_DEVICE_INIT(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def E_DEVICE_READY(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def E_DEVICE_RESET(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def CMD_RUNNING(self) -> bytes:
        raise NotImplementedError
    
    @CMD_RUNNING.setter
    @abstractmethod
    def CMD_RUNNING(self, cmd: bytes):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def DEV_PORT(self) -> bytes:
        raise NotImplementedError
    
    @DEV_PORT.setter
    @abstractmethod
    def DEV_PORT(self, cmd: bytes) -> bytes:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def DEV_NAME(self) -> bytes:
        raise NotImplementedError
    
    @DEV_NAME.setter
    @abstractmethod
    def DEV_NAME(self, name: bytes):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def DEV_CMD_LIST(self) -> {}:
        raise NotImplementedError