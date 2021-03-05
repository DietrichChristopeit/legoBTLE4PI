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
from asyncio import Event

from LegoBTLE.LegoWP.messages.downstream import CMD_EXT_SRV_CONNECT_REQ, CMD_EXT_SRV_DISCONNECT_REQ, DOWNSTREAM_MESSAGE
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, EXT_SERVER_NOTIFICATION,
    HUB_ACTION_NOTIFICATION,
    HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK,
    )
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG


class Device(ABC):
    proceed: Event = Event()
    proceed.set()
    
    @property
    @abstractmethod
    def command_executed(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port(self) -> bytes:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port2hub_connected(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def ext_srv_connected(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def ext_srv_disconnected(self) -> Event:
        raise NotImplementedError

    async def EXT_SRV_CONNECT_REQ(self, wait: bool = False) -> DOWNSTREAM_MESSAGE:
        await Device.proceed.wait()
        if wait:
            Device.proceed.clear()
        return CMD_EXT_SRV_CONNECT_REQ(port=self.port)

    async def EXT_SRV_DISCONNECT_REQ(self, wait: bool = False) -> DOWNSTREAM_MESSAGE:
        await Device.proceed.wait()
        if wait:
            Device.proceed.clear()
        return CMD_EXT_SRV_DISCONNECT_REQ(port=self.port)
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        raise NotImplementedError
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, notification: EXT_SERVER_NOTIFICATION):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def generic_error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        raise NotImplementedError
    
    @generic_error_notification.setter
    @abstractmethod
    def generic_error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        raise NotImplementedError
    
    @property
    def last_error(self) -> (bytes, bytes):
        if self.generic_error_notification is not None:
            return self.generic_error_notification.m_error_cmd, self.generic_error_notification.m_cmd_status
        else:
            return b'', b''
    
    @property
    @abstractmethod
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        raise NotImplementedError
    
    @hub_action_notification.setter
    @abstractmethod
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        raise NotImplementedError
    
    @hub_attached_io_notification.setter
    @abstractmethod
    def hub_attached_io_notification(self, io: HUB_ATTACHED_IO_NOTIFICATION):
        raise NotImplementedError

    @property
    @abstractmethod
    def cmd_feedback_notification_str(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        raise NotImplementedError

    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def command_feedback_log(self) -> [CMD_FEEDBACK_MSG]:
        raise NotImplementedError

    @command_feedback_log.setter
    @abstractmethod
    def command_feedback_log(self, feedback_msb: CMD_FEEDBACK_MSG):
        raise NotImplementedError
