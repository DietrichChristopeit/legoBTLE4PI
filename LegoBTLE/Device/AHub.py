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
from LegoBTLE.LegoWP.messages.downstream import (CMD_GENERAL_NOTIFICATION_HUB_REQ, CMD_HUB_ACTION_HUB_SND,
                                                 CMD_HUB_ALERT_HUB_SND, DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (DEV_GENERIC_ERROR, HUB_ACTION, HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO)
from LegoBTLE.LegoWP.types import HUB_ACTION_TYPE, HUB_ALERT_OPERATION, HUB_ALERT_TYPE


class Hub(Device):
    
    def __init__(self, name: str = 'LegoTechnicHub'):
        self._DEV_NAME = name
        self._DEV_PORT: bytes = b'\xff'
        self._hub_alert = None
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
    
    @generic_error.setter
    def generic_error(self, error: DEV_GENERIC_ERROR):
        self._last_error = error
        return
    
    @property
    def hub_action(self) -> HUB_ACTION:
        return self._hub_action
    
    @hub_action.setter
    def hub_action(self, action: HUB_ACTION):
        self._hub_action = action
        return
    
    def HUB_ACTION(self, action: bytes = HUB_ACTION_TYPE.DNS_HUB_INDICATE_BUSY_ON) -> CMD_HUB_ACTION_HUB_SND:
        return CMD_HUB_ACTION_HUB_SND(hub_action=action)
    
    @property
    def hub_attached_io(self) -> HUB_ATTACHED_IO:
        return self._hub_attached_io
    
    def GENERAL_NOTIFICATION_REQUEST(self) -> CMD_GENERAL_NOTIFICATION_HUB_REQ():
        return CMD_GENERAL_NOTIFICATION_HUB_REQ()
    
    def HUB_ALERT(self,
                  hub_alert: bytes = HUB_ALERT_TYPE.LOW_V,
                  hub_alert_op: bytes = HUB_ALERT_OPERATION.DNS_UPDATE_ENABLE) -> DOWNSTREAM_MESSAGE:
        try:
            assert hub_alert_op in (HUB_ALERT_OPERATION.DNS_UPDATE_ENABLE,
                                    HUB_ALERT_OPERATION.DNS_UPDATE_DISABLE,
                                    HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
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
