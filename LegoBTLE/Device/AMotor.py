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

from LegoBTLE.LegoWP.commands.downstream import CMD_GOTO_ABS_POS, DownStreamMessage, PORT_NOTIFICATION_REQ
from LegoBTLE.LegoWP.commands.upstream import (EXT_SERVER_MESSAGE_RCV, HUB_CMD_STATUS_RCV, HUB_PORT_NOTIFICATION_RCV,
                                               HUB_PORT_VALUE_RCV)
from LegoBTLE.LegoWP.types import MOVEMENT


class AMotor(ABC):

    @property
    @abstractmethod
    def port(self) -> bytes:
        raise NotImplementedError
    
    @port.setter
    @abstractmethod
    def port(self, port: bytes):
        raise NotImplementedError

    @property
    @abstractmethod
    def port_value_RCV(self) -> HUB_PORT_VALUE_RCV:
        raise NotImplementedError

    @port_value_RCV.setter
    @abstractmethod
    def port_value_RCV(self, port: HUB_PORT_VALUE_RCV):
        raise NotImplementedError

    @property
    @abstractmethod
    def gearRatio(self) -> float:
        raise NotImplementedError
    
    async def port_value_EFF(self):
        return await self.port_value_RCV.get_port_value_EFF(gear_ratio=self.gearRatio)
    
    @property
    @abstractmethod
    async def cmd_status_RCV(self) -> HUB_CMD_STATUS_RCV:
        raise NotImplementedError
    
    @property
    @abstractmethod
    async def ext_server_message_RCV(self) -> EXT_SERVER_MESSAGE_RCV:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def current_cmd_snd(self) -> DownStreamMessage:
        raise NotImplementedError
    
    @current_cmd_snd.setter
    @abstractmethod
    def current_cmd_snd(self, command: DownStreamMessage):
        raise NotImplementedError

    @abstractmethod
    async def port_free(self) -> bool:
        raise NotImplementedError
    
    def PORT_NOTIFICATION_REQ(self) -> PORT_NOTIFICATION_REQ:
        return PORT_NOTIFICATION_REQ(port=self.port)
    
    def GOTO_ABS_POS(self,
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
        return CMD_GOTO_ABS_POS(port=self.port,
                                start_cond=start_cond,
                                completion_cond=completion_cond,
                                speed=speed,
                                abs_pos=abs_pos,
                                abs_pos_a=abs_pos_a,
                                abs_pos_b=abs_pos_b,
                                abs_max_power=abs_max_power,
                                on_completion=on_completion,
                                use_profile=use_profile,
                                use_acc_profile=use_acc_profile,
                                use_decc_profile=use_decc_profile
                                )
    
    @property
    @abstractmethod
    async def port_notification_RCV(self) -> HUB_PORT_NOTIFICATION_RCV:
        raise NotImplementedError

    @port_notification_RCV.setter
    @abstractmethod
    def port_notification_RCV(self, notification: HUB_PORT_NOTIFICATION_RCV):
        raise NotImplementedError
