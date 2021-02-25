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
from datetime import datetime

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (CMD_MOVE_DEV_ABS_POS, CMD_START_MOVE_DEV, CMD_START_MOVE_DEV_DEGREES,
                                                 CMD_START_MOVE_DEV_TIME,
                                                 DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (DEV_CMD_STATUS, DEV_CURRENT_VALUE, DEV_GENERIC_ERROR_NOTIFICATION,
                                               DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION)
from LegoBTLE.LegoWP.types import EVENT_TYPE, MOVEMENT


class SingleMotor(AMotor):
    
    def __init__(self,
                 name: str = 'SingleMotor',
                 port: bytes = b'',
                 gearRatio: float = 1.0,
                 debug: bool = False):
        
        self._DEV_NAME: str = name
        self._port: bytes = port
        self._DEV_PORT = None
        self._gearRatio: float = gearRatio
        self._current_value = None
        self._last_port_value = None
        self._cmd_status: DEV_CMD_STATUS = None
        self._ext_srv_notification: EXT_SERVER_NOTIFICATION = None
        self._cmd_snt: DOWNSTREAM_MESSAGE = None
        self._port_notification: DEV_PORT_NOTIFICATION = None
        self._dev_port_connected: bool = False
        self._measure_distance_start = None
        self._measure_distance_end = None
        self._abs_max_distance = None
        self._generic_error_notification: DEV_GENERIC_ERROR_NOTIFICATION = None
        self._hub_action_notification: HUB_ACTION_NOTIFICATION = None
        self._hub_attached_io_notification: HUB_ATTACHED_IO_NOTIFICATION = None
        self._port_free: bool = True

        self._debug: bool = debug
        return

    @property
    def DEV_NAME(self) -> str:
        return self._DEV_NAME

    @DEV_NAME.setter
    def DEV_NAME(self, name: str):
        self._DEV_NAME = name
        return
    
    @property
    def DEV_PORT(self) -> bytes:
        return self._DEV_PORT

    @DEV_PORT.setter
    def DEV_PORT(self, port: bytes):
        self._DEV_PORT = port
        return

    @property
    def generic_error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._generic_error_notification

    @generic_error_notification.setter
    def generic_error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._generic_error_notification = error
        return
    
    @property
    def port_value(self) -> DEV_CURRENT_VALUE:
        return self._current_value
    
    @port_value.setter
    def port_value(self, new_value: DEV_CURRENT_VALUE):
        self._last_port_value = self._current_value
        self._current_value = new_value
        return

    @property
    def gearRatio(self) -> float:
        return self._gearRatio

    @property
    def cmd_status(self) -> DEV_CMD_STATUS:
        return self._cmd_status

    @cmd_status.setter
    def cmd_status(self, status: DEV_CMD_STATUS):
        self._cmd_status = status
        if self._cmd_status.m_cmd_status_str not in ('IDLE', 'EMPTY_BUF_CMD_COMPLETED'):
            self._port_free = False
        else:
            self._port_free = True
        return

    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification

    @ext_srv_notification.setter
    def ext_srv_notification(self, ext_srv_notification: EXT_SERVER_NOTIFICATION):
        self._ext_srv_notification = ext_srv_notification
        return
    
    @property
    def current_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        return self._cmd_snt

    @current_cmd_snt.setter
    def current_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        self._cmd_snt = command
        return

    @property
    def port_free(self) -> bool:
        return self._port_free
    
    @port_free.setter
    def port_free(self, status: bool):
        self._port_free = status
        return
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        return self._port_notification

    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        self._port_notification = notification
        if notification.m_event == EVENT_TYPE.IO_ATTACHED:
            self._DEV_PORT = notification.m_port[0]
            self._dev_port_connected = True
        if notification.m_event == EVENT_TYPE.IO_DETACHED:
            self._DEV_PORT = None
            self._dev_port_connected = False
        return

    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action

    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action_notification = action
        return

    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io

    @hub_attached_io_notification.setter
    def hub_attached_io_notification(self, io: HUB_ATTACHED_IO_NOTIFICATION):
        self._hub_attached_io_notification = io
        return

    @property
    def measure_distance_start(self) -> (datetime, DEV_CURRENT_VALUE):
        self._measure_distance_start = (datetime.now(), self._current_value)
        return self._measure_distance_start

    @property
    def measure_distance_end(self) -> (datetime, DEV_CURRENT_VALUE):
        self._measure_distance_end = (datetime.now(), self._current_value)
        return self._measure_distance_end

    async def START_MOVE_DEGREES(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed: int = None,
            abs_max_power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_START_MOVE_DEV_DEGREES:
        await self.wait_port_free()
        current_command = CMD_START_MOVE_DEV_DEGREES(
            synced=False,
            port=self._DEV_PORT,
            start_cond=start_cond,
            completion_cond=completion_cond,
            degrees=degrees,
            speed=speed,
            abs_max_power=abs_max_power,
            on_completion=on_completion,
            use_profile=use_profile,
            use_acc_profile=use_acc_profile,
            use_decc_profile=use_decc_profile)
        self.current_cmd_snt = current_command
        return current_command

    async def START_SPEED_TIME(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            time: int = 0,
            speed: int = None,
            direction: MOVEMENT = MOVEMENT.FORWARD,
            power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_START_MOVE_DEV_TIME:
        await self.wait_port_free()
        current_command = CMD_START_MOVE_DEV_TIME(
            port=self._DEV_PORT,
            start_cond=start_cond,
            completion_cond=completion_cond,
            time=time,
            speed=speed,
            direction=direction,
            power=power,
            on_completion=on_completion,
            use_profile=use_profile,
            use_acc_profile=use_acc_profile,
            use_decc_profile=use_decc_profile
            )
        self.current_cmd_snt = current_command
        return current_command

    async def GOTO_ABS_POS(
            self,
            start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed=0,
            abs_pos=None,
            abs_max_power=0,
            on_completion=MOVEMENT.BREAK,
            use_profile=0,
            use_acc_profile=MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_MOVE_DEV_ABS_POS:
        await self.wait_port_free()
        current_command = CMD_MOVE_DEV_ABS_POS(
            synced=False,
            port=self._DEV_PORT,
            start_cond=start_cond,
            completion_cond=completion_cond,
            speed=speed,
            abs_pos=abs_pos,
            abs_max_power=abs_max_power,
            on_completion=on_completion,
            use_profile=use_profile,
            use_acc_profile=use_acc_profile,
            use_decc_profile=use_decc_profile)
        self.current_cmd_snt = current_command
        return current_command

    async def START_SPEED(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed_ccw: int = None,
            speed_cw: int = None,
            abs_max_power: int = 0,
            profile_nr: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_START_MOVE_DEV:
        await self.wait_port_free()
        current_command = CMD_START_MOVE_DEV(
            synced=False,
            port=self._DEV_PORT,
            start_cond=start_cond,
            completion_cond=completion_cond,
            speed_ccw=speed_ccw,
            speed_cw=speed_cw,
            abs_max_power=abs_max_power,
            profile_nr=profile_nr,
            use_acc_profile=use_acc_profile,
            use_decc_profile=use_decc_profile
            )
        self.current_cmd_snt = current_command
        return current_command

