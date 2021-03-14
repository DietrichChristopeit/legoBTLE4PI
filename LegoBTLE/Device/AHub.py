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
import typing
from asyncio import Condition, Event
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_GENERAL_NOTIFICATION_HUB_REQ, CMD_HUB_ACTION_HUB_SND,
    DOWNSTREAM_MESSAGE, HUB_ALERT_NOTIFICATION_REQ,
    )
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK, PORT_VALUE,
    )
from LegoBTLE.LegoWP.types import (
    ALERT_STATUS, CMD_FEEDBACK_MSG, CMD_RETURN_CODE, HUB_ACTION, HUB_ALERT_OP, HUB_ALERT_TYPE,
    PERIPHERAL_EVENT,
    )


class Hub(Device):
    
    def __init__(self, server, name: str = 'LegoTechnicHub', debug: bool = False):
        
        self._name: str = name
        
        self._server = server
        self._connection: (StreamReader, StreamWriter) = None
        self._external_srv_notification: typing.Optional[EXT_SERVER_NOTIFICATION] = None
        self._external_srv_notification_log: [(datetime, EXT_SERVER_NOTIFICATION)] = []
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._last_cmd_snt: typing.Optional[DOWNSTREAM_MESSAGE] = None
        self._last_cmd_failed: typing.Optional[DOWNSTREAM_MESSAGE] = None
        self._port = b'\xfe'
        self._port2hub_connected: Event = Event()
        self._port2hub_connected.set()
        
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()
        
        self._cmd_return_code: typing.Optional[CMD_RETURN_CODE] = None
        
        self._cmd_feedback_notification: typing.Optional[PORT_CMD_FEEDBACK] = None
        self._cmd_feedback_log: [PORT_CMD_FEEDBACK] = []
        
        self._hub_attached_io_notification: typing.Optional[HUB_ATTACHED_IO_NOTIFICATION] = None
        
        self._hub_alert_notification: typing.Optional[HUB_ALERT_NOTIFICATION] = None
        self._hub_alert_notification_log: [(datetime, HUB_ALERT_NOTIFICATION)] = []
        self._hub_alert: Event = Event()
        self._hub_alert.clear()
        
        self._error_notification: typing.Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._error_notification_log: [(datetime, DEV_GENERIC_ERROR_NOTIFICATION)] = []
        self._hub_action_notification: typing.Optional[HUB_ACTION_NOTIFICATION] = None

        self._debug = debug
        
        return
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def port(self) -> bytes:
        return self._port
    
    @property
    def port2hub_connected(self) -> Event:
        raise UserWarning(f"NOT APPLICABLE for a hub")
    
    @property
    def ext_srv_connected(self) -> Event:
        return self._ext_srv_connected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._external_srv_notification
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, notification: EXT_SERVER_NOTIFICATION):
        if notification is not None:
            self._external_srv_notification = notification
            if self.debug:
                self.ext_srv_notification_log.append((datetime.timestamp(datetime.now()), notification))
            if notification.m_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED:
                self._ext_srv_connected.set()
            elif notification.m_event == PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED:
                self._ext_srv_connected.clear()
            return
        else:
            raise RuntimeError(f"NoneType Notification from Server received...")

    @property
    def ext_srv_notification_log(self) -> [(datetime, EXT_SERVER_NOTIFICATION)]:
        return self._external_srv_notification_log
    
    @property
    def error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._error_notification
    
    @error_notification.setter
    def error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._error_notification = error
        self._error_notification_log.append((datetime.timestamp(datetime.now()), error))
        return
    
    @property
    def error_notification_log(self) -> [(datetime, DEV_GENERIC_ERROR_NOTIFICATION)]:
        return self._error_notification_log
    
    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action_notification
    
    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action_notification = action
        return
    
    async def HUB_ACTION(self, action: bytes = HUB_ACTION.DNS_HUB_INDICATE_BUSY_ON) -> bool:
        current_command = CMD_HUB_ACTION_HUB_SND(hub_action=action)
        async with self._port_free_condition:
            print(f"{self._name}.HUB_ACTION WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.HUB_ACTION PASSED THE GATES...")
            await self.cmd_send(current_command)
            self.port_free_condition.notify_all()
        return True
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io_notification
    
    async def GENERAL_NOTIFICATION_REQUEST(self) -> bool:
        current_command = CMD_GENERAL_NOTIFICATION_HUB_REQ()
        async with self._port_free_condition:
            print(f"{self._name}.GENERAL_NOTIFICATION_REQUEST WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.GENERAL_NOTIFICATION_REQUEST PASSED THE GATES...")
            await self.cmd_send(current_command)
            self.port_free_condition.notify_all()
        return True
    
    async def HUB_ALERT_REQ(self,
                            hub_alert: bytes = HUB_ALERT_TYPE.LOW_V,
                            hub_alert_op: bytes = HUB_ALERT_OP.DNS_UPDATE_ENABLE) -> bool:
        try:
            assert hub_alert_op in (HUB_ALERT_OP.DNS_UPDATE_ENABLE,
                                    HUB_ALERT_OP.DNS_UPDATE_DISABLE,
                                    HUB_ALERT_OP.DNS_UDATE_REQUEST)
        except AssertionError:
            raise
        else:
            current_command = HUB_ALERT_NOTIFICATION_REQ(hub_alert=hub_alert, hub_alert_op=hub_alert_op)
            async with self._port_free_condition:
                print(f"{self._name}.HUB_ALERT_REQ WAITING AT THE GATES...")
                await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
                self._port_free.clear()
                print(f"{self._name}.HUB_ALERT_REQ PASSED THE GATES...")
                await self.cmd_send(current_command)
                self.port_free_condition.notify_all()
            return True
    
    @property
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        return self._hub_alert_notification
    
    @hub_alert_notification.setter
    def hub_alert_notification(self, alert: HUB_ALERT_NOTIFICATION):
        self._hub_alert_notification = alert
        self._hub_alert_notification_log.append((datetime.timestamp(datetime.now()), alert))
        self._hub_alert.set()
        if alert.hub_alert_status == ALERT_STATUS.ALERT:
            raise ResourceWarning(f"Hub Alert Received: {alert.hub_alert_type_str}")
    
    @property
    def hub_alert_notification_log(self) -> [(datetime, HUB_ALERT_NOTIFICATION)]:
        return self._hub_alert_notification_log

    def hub_alert(self) -> Event:
        return self._hub_alert
    
    @property
    def last_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        return self._last_cmd_snt
    
    @last_cmd_snt.setter
    def last_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        self._last_cmd_snt = command
        return

    @property
    def last_cmd_failed(self) -> DOWNSTREAM_MESSAGE:
        return self._last_cmd_failed

    @last_cmd_failed.setter
    def last_cmd_failed(self, cmd: DOWNSTREAM_MESSAGE):
        self._last_cmd_failed = cmd
        return

    @property
    def port_free_condition(self) -> Condition:
        return self._port_free_condition
    
    @property
    def port_free(self) -> Event:
        return self._port_free
    
    @property
    def cmd_return_code(self) -> CMD_RETURN_CODE:
        return self._cmd_return_code
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._cmd_feedback_notification
    
    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        self._cmd_feedback_notification = notification
        self._cmd_feedback_log.append(notification.m_cmd_feedback)
        return

    @property
    def cmd_feedback_log(self) -> [CMD_FEEDBACK_MSG]:
        return self._cmd_feedback_log
      
    @property
    def connection(self) -> (StreamReader, StreamWriter):
        return self._connection
    
    @connection.setter
    def connection(self, connection: [StreamReader, StreamWriter]):
        self._connection = connection
        return
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @server.setter
    def server(self, server: (int, str)):
        self._server = server
        
    @property
    def port_value(self) -> PORT_VALUE:
        raise NotImplemented
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise NotImplemented
    
    @property
    def debug(self) -> bool:
        return self._debug
