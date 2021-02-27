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
import asyncio

from LegoBTLE.Device.ADevice import Device

from LegoBTLE.LegoWP.messages.downstream import (
    CMD_GENERAL_NOTIFICATION_HUB_REQ,
    CMD_HUB_ACTION_HUB_SND,
    CMD_HUB_ALERT_HUB_SND,
    DOWNSTREAM_MESSAGE
    )

from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION,
    EXT_SERVER_NOTIFICATION,
    HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION,
    HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK
    )

from LegoBTLE.LegoWP.types import (
    HUB_ACTION,
    HUB_ALERT_CMD,
    HUB_ALERT, CMD_RETURN_CODE, CMD_FEEDBACK_MSG
    )


class Hub(Device):
    
    def __init__(self, name: str = 'LegoTechnicHub'):
        
        self._cmd_return_code: CMD_RETURN_CODE = None
        self._dev_srv_connected: bool = False
        self._DEV_NAME = name
        self._SRV_PORT: bytes = b'\xfe'
        self._DEV_PORT: bytes = self._SRV_PORT
        self._dev_port_connected: bool = False
        self._hub_alert = None
        self._last_error_notification = None
        self._hub_action_notification: HUB_ACTION_NOTIFICATION = None
        self._hub_attached_io_notification: HUB_ATTACHED_IO_NOTIFICATION = None
        self._external_srv_notification: EXT_SERVER_NOTIFICATION = None
        self._cmd_feedback_notification: PORT_CMD_FEEDBACK = None
        self._current_cmd_feedback: [CMD_FEEDBACK_MSG] = None
        return
    
    @property
    def DEV_NAME(self) -> str:
        return self._DEV_NAME
    
    @property
    def DEV_PORT(self) -> bytes:
        return self._DEV_PORT
    
    @property
    def dev_port_connected(self) -> bool:
        return self._dev_port_connected
    
    @dev_port_connected.setter
    def dev_port_connected(self, connected: bool):
        self._dev_port_connected = connected
        return
    
    @property
    def dev_srv_connected(self) -> bool:
        return self._dev_srv_connected
    
    @dev_srv_connected.setter
    def dev_srv_connected(self, connected: bool):
        self._dev_srv_connected = connected
        return
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._external_srv_notification
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, notification: EXT_SERVER_NOTIFICATION):
        
        if notification is not None:
            self._external_srv_notification = notification
            if notification.m_event_str == 'EXT_SRV_DISCONNECTED':
                self._dev_srv_connected = False
            return
        else:
            return
    
    @property
    def generic_error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._last_error_notification
    
    @generic_error_notification.setter
    def generic_error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._last_error_notification = error
        return
    
    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action_notification
    
    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action_notification = action
        return
    
    def HUB_ACTION(self, action: bytes = HUB_ACTION.DNS_HUB_INDICATE_BUSY_ON) -> CMD_HUB_ACTION_HUB_SND:
        return CMD_HUB_ACTION_HUB_SND(hub_action=action)
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io_notification
    
    def GENERAL_NOTIFICATION_REQUEST(self) -> CMD_GENERAL_NOTIFICATION_HUB_REQ():
        return CMD_GENERAL_NOTIFICATION_HUB_REQ()
    
    def HUB_ALERT(self,
                  hub_alert: bytes = HUB_ALERT.LOW_V,
                  hub_alert_op: bytes = HUB_ALERT_CMD.DNS_UPDATE_ENABLE) -> DOWNSTREAM_MESSAGE:
        try:
            assert hub_alert_op in (HUB_ALERT_CMD.DNS_UPDATE_ENABLE,
                                    HUB_ALERT_CMD.DNS_UPDATE_DISABLE,
                                    HUB_ALERT_CMD.DNS_UDATE_REQUEST)
        except AssertionError:
            raise
        else:
            return CMD_HUB_ALERT_HUB_SND(hub_alert=hub_alert, hub_alert_op=hub_alert_op)
    
    @property
    def hub_alert(self) -> HUB_ALERT_NOTIFICATION:
        return self._hub_alert
    
    @hub_alert.setter
    def hub_alert(self, alert: HUB_ALERT_NOTIFICATION):
        self._hub_alert = alert
        return
    
    async def wait_hub_alert(self, alert: HUB_ALERT_NOTIFICATION) -> bool:
        while self.hub_alert.hub_alert != alert.hub_alert:
            await asyncio.sleep(.001)
        return True
    
    @property
    def cmd_return_code(self) -> CMD_RETURN_CODE:
        return self._cmd_return_code
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._cmd_feedback_notification
    
    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        self._cmd_feedback_notification = notification
        self._current_cmd_feedback.append(notification.m_cmd_feedback)
        return
    
    @property
    def current_cmd_feedback(self) -> [CMD_FEEDBACK_MSG]:
        return self._current_cmd_feedback
