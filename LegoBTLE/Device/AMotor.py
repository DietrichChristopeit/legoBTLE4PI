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
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.messages.downstream import (CMD_MOVE_DEV_ABS_POS, CMD_PORT_NOTIFICATION_DEV_REQ, CMD_START_MOVE_DEV,
                                                 CMD_START_MOVE_DEV_DEGREES, CMD_START_MOVE_DEV_TIME, DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (DEV_CMD_STATUS, DEV_CURRENT_VALUE, DEV_PORT_NOTIFICATION,
                                               EXT_SERVER_MESSAGE)
from LegoBTLE.LegoWP.types import MOVEMENT


class AMotor(ABC, Device):
    
    @property
    @abstractmethod
    def DEV_PORT(self) -> bytes:
        raise NotImplementedError
    
    @DEV_PORT.setter
    @abstractmethod
    def DEV_PORT(self, port: bytes):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def DEV_NAME(self):
        raise NotImplementedError
    
    @DEV_NAME.setter
    @abstractmethod
    def DEV_NAME(self, port: bytes):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port_value(self) -> DEV_CURRENT_VALUE:
        raise NotImplementedError
    
    @port_value.setter
    @abstractmethod
    def port_value(self, port: DEV_CURRENT_VALUE):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def gearRatio(self) -> float:
        raise NotImplementedError
    
    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF()
    
    @property
    @abstractmethod
    def cmd_status(self) -> DEV_CMD_STATUS:
        raise NotImplementedError
    
    @cmd_status.setter
    @abstractmethod
    def cmd_status(self, status: DEV_CMD_STATUS):
        raise NotImplementedError
    
    async def wait_cmd_executed(self) -> bool:
        while (self.cmd_status is None) or (self.cmd_status.m_cmd_status_str not in ('IDLE',
                                                                                     'EMPTY_BUF_CMD_COMPLETED')):
            await asyncio.sleep(.001)
        return True
    
    @property
    @abstractmethod
    def ext_server_message(self) -> EXT_SERVER_MESSAGE:
        raise NotImplementedError
    
    async def wait_ext_server_connected(self) -> bool:
        while (self.ext_server_message is None) or (self.ext_server_message.m_cmd_code_str != 'EXT_SRV_CONNECTED'):
            await asyncio.sleep(.001)
        return True
    
    async def wait_ext_server_disconnected(self) -> bool:
        while (self.ext_server_message is None) or (self.ext_server_message.m_cmd_code_str != 'EXT_SRV_DISCONNECTED'):
            await asyncio.sleep(.001)
        return True
    
    @property
    @abstractmethod
    def current_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        raise NotImplementedError
    
    @current_cmd_snt.setter
    @abstractmethod
    def current_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port_free(self) -> bool:
        raise NotImplementedError
    
    @port_free.setter
    @abstractmethod
    def port_free(self, status: bool):
        raise NotImplementedError
    
    @abstractmethod
    async def wait_port_free(self) -> bool:
        while not self.port_free:
            await asyncio.sleep(.001)
        return True
    
    def REQ_PORT_NOTIFICATION(self) -> CMD_PORT_NOTIFICATION_DEV_REQ:
        current_command = CMD_PORT_NOTIFICATION_DEV_REQ(port=self.DEV_PORT)
        self.current_cmd_snt = current_command
        return current_command
    
    async def GOTO_ABS_POS(
            self,
            start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed=0,
            abs_pos=None,
            abs_pos_a=None,
            abs_pos_b=None,
            abs_max_power=0,
            on_completion=MOVEMENT.BREAK,
            use_profile=0,
            use_acc_profile=MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE
            ) -> CMD_MOVE_DEV_ABS_POS:
        if await self.wait_port_free():
            if isinstance(self, SingleMotor):
                current_command = CMD_MOVE_DEV_ABS_POS(
                    synced=False,
                    port=self.DEV_PORT,
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
            elif isinstance(self, SynchronizedMotor):
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
            speed_ccw: int = None,
            speed_cw: int = None,
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
            if isinstance(self, SingleMotor):
                current_command = CMD_START_MOVE_DEV(
                    synced=False,
                    port=self.DEV_PORT,
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
            elif isinstance(self, SynchronizedMotor):
                current_command = CMD_START_MOVE_DEV(
                    synced=True,
                    port=self.DEV_PORT,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed_ccw=speed_ccw,
                    speed_cw=speed_cw,
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
    
    async def START_SPEED_DEGREES(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed: int = None,
            speed_a: int = None,
            speed_b: int = None,
            abs_max_power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
            ):
        if await self.wait_port_free():
            if isinstance(self, SingleMotor):
                current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=False,
                    port=self.DEV_PORT,
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
            elif isinstance(self, SynchronizedMotor):
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
    
    def START_SPEED_TIME(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            time: int = 0,
            speed: int = None,
            direction: MOVEMENT = MOVEMENT.FORWARD,
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
            if isinstance(self, SingleMotor):
                current_command = CMD_START_MOVE_DEV_TIME(
                    port=self.DEV_PORT,
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
            elif isinstance(self, SynchronizedMotor):
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
    
    @property
    @abstractmethod
    def DEV_PORT_connected(self) -> bool:
        raise NotImplementedError
    
    @DEV_PORT_connected.setter
    @abstractmethod
    def DEV_PORT_connected(self, connected: bool):
        raise NotImplementedError
    
    async def wait_port_connected(self) -> bool:
        while (self.DEV_PORT_connected is None) or not self.DEV_PORT_connected:
            await asyncio.sleep(.001)
        return True
    
    @property
    @abstractmethod
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise NotImplementedError
    
    @port_notification.setter
    @abstractmethod
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        raise NotImplementedError
    
    async def wait_port_notification(self) -> bool:
        while self.port_notification is None:
            await asyncio.sleep(.001)
        return True
    
    @property
    @abstractmethod
    def measure_distance_start(self) -> (datetime, DEV_CURRENT_VALUE):
        raise NotImplementedError
    
    @measure_distance_start.setter
    @abstractmethod
    def measure_distance_start(self, tal: (datetime, DEV_CURRENT_VALUE) = (datetime.now(), port_value)):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def measure_distance_end(self) -> (datetime, DEV_CURRENT_VALUE):
        raise NotImplementedError
    
    @measure_distance_end.setter
    @abstractmethod
    def measure_distance_end(self, tal: (datetime, DEV_CURRENT_VALUE) = (datetime.now(), port_value)):
        raise NotImplementedError
    
    def distance_start_end(self, gearRatio=None) -> {float, float, float}:
        if gearRatio is None:
            gearRatio = self.gearRatio
        dt = {}
        for (k, x1) in self.measure_distance_end[1].items():
            dt[k] = (x1[k] - self.measure_distance_start[1][k]) / gearRatio
        return dt
    
    def avg_speed(self, gearRatio=None) -> {float, float, float}:
        if gearRatio is None:
            gearRatio = self.gearRatio
        v = {}
        dt = self.measure_distance_end[0] - self.measure_distance_start[0]
        for (k, d) in self.distance_start_end(gearRatio=gearRatio).items():
            v[k] = d / dt
        return v
