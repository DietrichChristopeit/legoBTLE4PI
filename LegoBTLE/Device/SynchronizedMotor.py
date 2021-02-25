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
from LegoBTLE.LegoWP.messages.downstream import (CMD_MOVE_DEV_ABS_POS, CMD_SETUP_DEV_VIRTUAL_PORT, CMD_START_MOVE_DEV,
                                                 CMD_START_MOVE_DEV_DEGREES,
                                                 CMD_START_MOVE_DEV_TIME, DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (DEV_CMD_STATUS, DEV_VALUE, DEV_GENERIC_ERROR_NOTIFICATION,
                                               DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION)
from LegoBTLE.LegoWP.types import CONNECTION_TYPE, MOVEMENT, PORT


class SynchronizedMotor(AMotor):


    def __init__(self,
                 name: str = 'SynchronizedMotor',
                 motor_a: AMotor = None,
                 motor_b: AMotor = None,
                 debug: bool = False):
        
        self._DEV_NAME = name
        self._DEV_PORT = None
        self._DEV_PORT_connected: bool = False
        self._port_notification = None
        self._motor_a: AMotor = motor_a
        self._gearRatio: {float, float} = {1.0, 1.0}
        self._motor_a_port: bytes= motor_a.DEV_PORT
        self._motor_b: AMotor = motor_b
        self._motor_b_port: bytes = motor_b.DEV_PORT
        self._current_value = None
        self._last_value = None
        self._generic_error = None
        self._hub_action = None
        self._hub_attached_io = None
        self._port_free = True
        self._cmd_status = None
        self._current_cmd = None
        self._measure_distance_start = None
        self._measure_distance_end = None
        self._ext_srv_notification: EXT_SERVER_NOTIFICATION = None
        
        self._debug = debug
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
    def is_connected(self) -> bool:
        return self._DEV_PORT_connected
    
    @property
    def first_motor_port(self) -> bytes:
        return PORT(self._motor_a_port).value
    
    @property
    def second_motor_port(self) -> bytes:
        return PORT(self._motor_b_port).value

    @property
    def first_motor(self) -> AMotor:
        return self._motor_a

    @property
    def second_motor(self) -> AMotor:
        return self._motor_b

    @property
    def gearRatio(self) -> {float, float}:
        return {self._gearRatio, self._gearRatio}

    @gearRatio.setter
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0):
        self._gearRatio = {gearRatio_motor_a, gearRatio_motor_b}
        return

    @property
    def dev_port_connected(self) -> bool:
        return self._DEV_PORT_connected

    @property
    def measure_distance_start(self) -> (datetime, DEV_VALUE):
        self._measure_distance_start = (datetime.now(), self._current_value)
        return self._measure_distance_start

    @property
    def measure_distance_end(self) -> (datetime, DEV_VALUE):
        self._measure_distance_end = (datetime.now(), self._current_value)
        return self._measure_distance_end

    async def VIRTUAL_PORT_SETUP(
            self,
            connect: bool = True
            ) -> CMD_SETUP_DEV_VIRTUAL_PORT:
        
        if connect:
            vps = CMD_SETUP_DEV_VIRTUAL_PORT(
                connectionType=CONNECTION_TYPE.CONNECT,
                port_a=PORT(self._motor_a_port).value,
                port_b=PORT(self._motor_b_port).value
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
    def port_value(self) -> DEV_VALUE:
        return self._current_value
    
    @port_value.setter
    def port_value(self, new_value: DEV_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return
    
    @property
    def generic_error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._generic_error
    
    @generic_error_notification.setter
    def generic_error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._generic_error = error
        return
    
    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action
    
    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action = action
        return
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io
    
    @hub_attached_io_notification.setter
    def hub_attached_io_notification(self, io: HUB_ATTACHED_IO_NOTIFICATION):
        self._hub_attached_io = io
        self._DEV_PORT = io.m_port
        self._motor_a_port = PORT(io.m_vport_a)
        self._motor_b_port = PORT(io.m_vport_b)
        return

    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, ext_srv_notification: EXT_SERVER_NOTIFICATION):
        self._ext_srv_notification = ext_srv_notification
        return
    
    @property
    def port_free(self) -> bool:
        return self._port_free
    
    @port_free.setter
    def port_free(self, status: bool):
        self._port_free = status
        self._motor_a.port_free = status
        self._motor_b.port_free = status
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
            self._port_free = False
            self._motor_a.port_free = False
            self._motor_b.port_free = False
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
            self._port_free = False
            self._motor_a.port_free = False
            self._motor_b.port_free = False
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
            self._port_free = False
            self._motor_a.port_free = False
            self._motor_b.port_free = False
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
            self._port_free = False
            self._motor_a.port_free = False
            self._motor_b.port_free = False
            return current_command
