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

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (CMD_MOVE_DEV_ABS_POS, CMD_SETUP_DEV_VIRTUAL_PORT, CMD_START_MOVE_DEV,
                                                 CMD_START_MOVE_DEV_DEGREES,
                                                 CMD_START_MOVE_DEV_TIME, DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (DEV_CMD_STATUS, DEV_GENERIC_ERROR, DEV_PORT_NOTIFICATION,
                                               DEV_CURRENT_VALUE,
                                               EXT_SERVER_MESSAGE, HUB_ACTION,
                                               HUB_ATTACHED_IO)
from LegoBTLE.LegoWP.types import CONNECTION_TYPE, MOVEMENT, PORT


class SynchronizedMotor(Device, AMotor):
    
    def __init__(self,
                 name: str = 'SynchronizedMotor',
                 motor_a: PORT = None,
                 motor_b: PORT = None,
                 debug: bool = False):
        
        self._name = name
        self._DEV_PORT = None
        self._DEV_PORT_connected: bool = False
        self._port_notification = None
        self._motor_a: PORT = motor_a
        self._motor_b: PORT = motor_b
        self._current_value = None
        self._last_value = None
        self._generic_error = None
        self._hub_action = None
        self._hub_attached_io = None
        self._ext_server_message = None
        self._port_free = True
        self._cmd_status = None
        self._current_cmd = None
        self._measure_distance_start = None
        self._measure_distance_end = None
        
        self._debug = debug
        return
    
    @property
    def is_connected(self) -> bool:
        return self._DEV_PORT_connected
    
    @property
    def first_motor(self) -> bytes:
        return PORT(self._motor_a).value
    
    @property
    def second_motor(self) -> bytes:
        return PORT(self._motor_b).value

    @property
    def measure_distance_start(self) -> (datetime, DEV_CURRENT_VALUE):
        self._measure_distance_start = (datetime.now(), self._current_value)
        return self._measure_distance_start

    @property
    def measure_distance_end(self) -> (datetime, DEV_CURRENT_VALUE):
        self._measure_distance_end = (datetime.now(), self._current_value)
        return self._measure_distance_end

    async def VIRTUAL_PORT_SETUP(
            self,
            connect: bool = True
            ) -> CMD_SETUP_DEV_VIRTUAL_PORT:
        
        if connect:
            vps = CMD_SETUP_DEV_VIRTUAL_PORT(
                connectionType=CONNECTION_TYPE.CONNECT,
                port_a=PORT(self._motor_a).value,
                port_b=PORT(self._motor_b).value
                )
            self._current_cmd = vps
            return vps
        else:
            vps = CMD_SETUP_DEV_VIRTUAL_PORT(
                connectionType=CONNECTION_TYPE.DISCONNECT,
                port=self._DEV_PORT
                )
            return vps
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise Warning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        raise Warning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @property
    def port_value(self) -> DEV_CURRENT_VALUE:
        return self._current_value
    
    @port_value.setter
    def port_value(self, new_value: DEV_CURRENT_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return
    
    @property
    def generic_error(self) -> DEV_GENERIC_ERROR:
        return self._generic_error
    
    @generic_error.setter
    def generic_error(self, error: DEV_GENERIC_ERROR):
        self._generic_error = error
        return
    
    @property
    def hub_action(self) -> HUB_ACTION:
        return self._hub_action
    
    @hub_action.setter
    def hub_action(self, action: HUB_ACTION):
        self._hub_action = action
        return
    
    @property
    def hub_attached_io(self) -> HUB_ATTACHED_IO:
        return self._hub_attached_io
    
    @hub_attached_io.setter
    def hub_attached_io(self, io: HUB_ATTACHED_IO):
        self._hub_attached_io = io
        self._DEV_PORT = io.m_port
        self._motor_a = PORT(io.m_vport_a)
        self._motor_b = PORT(io.m_vport_b)
        return
    
    @property
    def ext_server_message(self) -> EXT_SERVER_MESSAGE:
        return self._ext_server_message
    
    @ext_server_message.setter
    def ext_server_message(self, external_msg: EXT_SERVER_MESSAGE):
        self._ext_server_message = external_msg
        return
    
    @property
    def port_free(self) -> bool:
        return self._port_free
    
    @port_free.setter
    def port_free(self, status: bool):
        self._port_free = status
        return
    
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
    def current_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        return self._current_cmd
    
    @current_cmd_snt.setter
    def current_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        self._current_cmd = command
        return
    
    async def START_MOVE_DEGREES(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed_a: int = None,
            speed_b: int = None,
            abs_max_power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_START_MOVE_DEV_DEGREES:
        if await self.wait_port_free():
            current_command = CMD_START_MOVE_DEV_DEGREES(
                synced=True,
                port=self.DEV_PORT,
                start_cond=start_cond,
                completion_cond=completion_cond,
                degrees=degrees,
                speed_a=speed_a,
                speed_b=speed_b,
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
            speed_a: int = None,
            direction_a: MOVEMENT = MOVEMENT.FORWARD,
            speed_b: int = None,
            direction_b: MOVEMENT = MOVEMENT.FORWARD,
            power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_START_MOVE_DEV_TIME:
        if await self.wait_port_free():
            current_command = CMD_START_MOVE_DEV_TIME(
                port=self.DEV_PORT,
                start_cond=start_cond,
                completion_cond=completion_cond,
                time=time,
                speed_a=speed_a,
                direction_a=direction_a,
                speed_b=speed_b,
                direction_b=direction_b,
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
            abs_pos_a=None,
            abs_pos_b=None,
            abs_max_power=0,
            on_completion=MOVEMENT.BREAK,
            use_profile=0,
            use_acc_profile=MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_MOVE_DEV_ABS_POS:
        if await self.wait_port_free():
            current_command = CMD_MOVE_DEV_ABS_POS(
                synced=True,
                port=self.DEV_PORT,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed=speed,
                abs_pos_a=abs_pos_a,
                abs_pos_b=abs_pos_b,
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
            speed_ccw_1: int = None,
            speed_cw_1: int = None,
            speed_ccw_2: int = None,
            speed_cw_2: int = None,
            abs_max_power: int = 0,
            profile_nr: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ):
        if await self.wait_port_free():
            current_command = CMD_START_MOVE_DEV(
                synced=True,
                port=self.DEV_PORT,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed_ccw_1=speed_ccw_1,
                speed_cw_1=speed_cw_1,
                speed_ccw_2=speed_ccw_2,
                speed_cw_2=speed_cw_2,
                abs_max_power=abs_max_power,
                profile_nr=profile_nr,
                use_acc_profile=use_acc_profile,
                use_decc_profile=use_decc_profile)
            self.current_cmd_snt = current_command
            return current_command
