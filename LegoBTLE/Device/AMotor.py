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
from abc import ABC, abstractmethod
from datetime import datetime

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.commands.downstream import (CMD_GOTO_ABS_POS, CMD_PORT_NOTIFICATION_REQ, CMD_START_SPEED,
                                                 CMD_START_SPEED_DEGREES, CMD_START_SPEED_TIME, DownStreamMessage)
from LegoBTLE.LegoWP.commands.upstream import (DEV_CMD_STATUS_RCV, DEV_PORT_NOTIFICATION_RCV, DEV_PORT_VALUE,
                                               EXT_SERVER_MESSAGE_RCV)
from LegoBTLE.LegoWP.types import MOVEMENT


class AMotor(ABC, Device):
    
    @property
    @abstractmethod
    def DEV_PORT(self):
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
    def port_value(self) -> DEV_PORT_VALUE:
        raise NotImplementedError
    
    @port_value.setter
    @abstractmethod
    def port_value(self, port: DEV_PORT_VALUE):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def gearRatio(self) -> float:
        raise NotImplementedError
    
    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF()
    
    @property
    @abstractmethod
    def cmd_status(self) -> DEV_CMD_STATUS_RCV:
        raise NotImplementedError
    
    async def wait_cmd_executed(self) -> bool:
        st = False
        while not st:
            st = True
            for s in self.cmd_status.m_cmd_status_str:
                if s not in ('EMPTY_BUF_CMD_COMPLETED', 'IDLE'):
                    st = st and False
                    await asyncio.sleep(0.001)
                    continue
                else:
                    st = st and True
            if st:
                return True
    
    @property
    @abstractmethod
    def ext_server_message_RCV(self) -> EXT_SERVER_MESSAGE_RCV:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def current_cmd_snt(self) -> DownStreamMessage:
        raise NotImplementedError
    
    @current_cmd_snt.setter
    @abstractmethod
    def current_cmd_snt(self, command: DownStreamMessage):
        raise NotImplementedError
    
    @abstractmethod
    async def port_free(self) -> bool:
        raise NotImplementedError
    
    def REQ_PORT_NOTIFICATION(self) -> CMD_PORT_NOTIFICATION_REQ:
        return CMD_PORT_NOTIFICATION_REQ(port=self.DEV_PORT)
    
    def GOTO_ABS_POS(
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
            ) -> CMD_GOTO_ABS_POS:
        
        if isinstance(self, SingleMotor):
            return CMD_GOTO_ABS_POS(
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
        elif isinstance(self, SynchronizedMotor):
            return CMD_GOTO_ABS_POS(
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
    
    def START_SPEED(
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
        if isinstance(self, SingleMotor):
            return CMD_START_SPEED(
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
        elif isinstance(self, SynchronizedMotor):
            return CMD_START_SPEED(
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
    
    def START_SPEED_DEGREES(
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
        if isinstance(self, SingleMotor):
            return CMD_START_SPEED_DEGREES(
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
        elif isinstance(self, SynchronizedMotor):
            return CMD_START_SPEED_DEGREES(
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
            ) -> CMD_START_SPEED_TIME:
        return CMD_START_SPEED_TIME(
            port=self.DEV_PORT,
            start_cond=start_cond,
            completion_cond=completion_cond,
            time=time,
            speed=speed,
            direction=direction,
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
    
    @property
    @abstractmethod
    def DEV_PORT_connected(self) -> bool:
        raise NotImplementedError
    
    @DEV_PORT_connected.setter
    @abstractmethod
    def DEV_PORT_connected(self, connected: bool):
        raise NotImplementedError
    
    async def wait_port_connected(self) -> bool:
        while not self.DEV_PORT_connected:
            await asyncio.sleep(0.001)
        return True
    
    @property
    @abstractmethod
    def port_notification(self) -> DEV_PORT_NOTIFICATION_RCV:
        raise NotImplementedError
    
    @port_notification.setter
    @abstractmethod
    def port_notification(self, notification: DEV_PORT_NOTIFICATION_RCV):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def measure_distance_start(self) -> (datetime, DEV_PORT_VALUE):
        raise NotImplementedError

    @measure_distance_start.setter
    @abstractmethod
    def measure_distance_start(self, tal: (datetime, DEV_PORT_VALUE) = (datetime.now(), port_value)):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def measure_distance_end(self) -> (datetime, DEV_PORT_VALUE):
        raise NotImplementedError

    @measure_distance_end.setter
    @abstractmethod
    def measure_distance_end(self, tal: (datetime, DEV_PORT_VALUE) = (datetime.now(), port_value)):
        raise NotImplementedError
    
    def distance_start_end(self, gearRatio=None) -> {float, float, float}:
        if gearRatio is None:
            gearRatio = self.gearRatio
        return self.measure_distance_end[1].get_port_value_EFF(gearRatio) - \
               self.measure_distance_start[1].get_port_value_EFF(gearRatio)

    def avg_speed(self) -> float:
        return (self.measure_distance_end[0] - self.measure_distance_start[0]) / self.distance_start_end(
            self.gearRatio)[0]
