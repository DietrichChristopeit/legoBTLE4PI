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
from typing import Optional
from asyncio import Condition, Event
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_MOVE_DEV_ABS_POS, CMD_START_MOVE_DEV, CMD_START_MOVE_DEV_DEGREES,
    CMD_START_MOVE_DEV_TIME,
    DOWNSTREAM_MESSAGE,
    )
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_VALUE, DEV_GENERIC_ERROR_NOTIFICATION,
    DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION, HUB_ALERT_NOTIFICATION,
    HUB_ATTACHED_IO_NOTIFICATION,
    PORT_CMD_FEEDBACK,
    )
from LegoBTLE.LegoWP.types import PERIPHERAL_EVENT, MOVEMENT, CMD_FEEDBACK_MSG


class SingleMotor(AMotor):

    def __init__(self,
                 server: tuple[str, int],
                 port: bytes,
                 name: str = 'SingleMotor',
                 gearRatio: float = 1.0,
                 debug: bool = False,
                 ):
        """

        :type server: object
        """
        self._name: str = name
        self._port: bytes = port

        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()
        
        self._last_cmd_snt: Optional[DOWNSTREAM_MESSAGE] = None
        self._last_cmd_failed: Optional[DOWNSTREAM_MESSAGE] = None
        
        self._current_cmd_feedback_notification: Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: Optional[str] = None
        self._command_feedback_log: Optional[list[CMD_FEEDBACK_MSG]] = None
        
        self._server: [str, int] = server
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._connection: (StreamReader, StreamWriter) = None
        
        self._port_notification: Optional[DEV_PORT_NOTIFICATION] = None
        self._port2hub_connected: Event = Event()
        self._port2hub_connected.clear()
        
        self._gearRatio: {float, float} = {gearRatio, gearRatio}
        self._current_value: Optional[DEV_VALUE] = None
        self._last_value: Optional[DEV_VALUE] = None
        
        self._measure_distance_start = None
        self._measure_distance_end = None
        self._abs_max_distance = None
        self._generic_error_notification: Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._hub_action_notification: Optional[HUB_ACTION_NOTIFICATION] = None
        self._hub_attached_io_notification: Optional[HUB_ATTACHED_IO_NOTIFICATION] = None
        
        self._debug: bool = debug
        return
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str):
        self._name = name
        return
    
    @property
    def port(self) -> bytes:
        return self._port
    
    @port.setter
    def port(self, port: bytes):
        self._port = port
        return

    @property
    def port2hub_connected(self) -> Event:
        return self._port2hub_connected

    @property
    def port_value(self) -> DEV_VALUE:
        return self._current_value

    @port_value.setter
    def port_value(self, new_value: DEV_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return
    
    @property
    def port_free_condition(self) -> Condition:
        return self._port_free_condition

    @property
    def port_free(self) -> Event:
        return self._port_free

    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        return self._port_notification

    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        self._port_notification = notification
        return
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @server.setter
    def server(self, server: (int, str)):
        self._server = server
    
    @property
    def connection(self) -> (StreamReader, StreamWriter):
        return self._connection
    
    @connection.setter
    def connection(self, connection: [StreamReader, StreamWriter]):
        self._connection = connection
        return
    
    @property
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        raise NotImplemented(f"HUB NOTIFICATION FOR {type(self)} NOT APPLICABLE")
    
    @hub_alert_notification.setter
    def hub_alert_notification(self, notification: HUB_ALERT_NOTIFICATION):
        pass
    
    @property
    def generic_error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._generic_error_notification
    
    @generic_error_notification.setter
    def generic_error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._generic_error_notification = error
        return
 
    @property
    def gearRatio(self) -> {float, float}:
        return {self._gearRatio, self._gearRatio}
    
    @gearRatio.setter
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0):
        self._gearRatio = {gearRatio_motor_a, gearRatio_motor_b}
        return
    
    @property
    def ext_srv_connected(self) -> Event:
        return self._ext_srv_connected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, ext_srv_notification: EXT_SERVER_NOTIFICATION):
        self._ext_srv_notification = ext_srv_notification
        if self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED:
            self._ext_srv_connected.set()
            self._port_free.set()
        elif self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED:
            self._ext_srv_connected.clear()
        return
    
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
    def last_cmd_failed(self, command: DOWNSTREAM_MESSAGE):
        self._last_cmd_failed = command
        return
    
    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action_notification
    
    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action_notification = action
        return
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io_notification
    
    @hub_attached_io_notification.setter
    def hub_attached_io_notification(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        self._hub_attached_io_notification = io_notification
        if io_notification.m_event == PERIPHERAL_EVENT.IO_ATTACHED:
            self._port2hub_connected.set()
            self._port_free.set()
        elif io_notification.m_event == PERIPHERAL_EVENT.IO_DETACHED:
            self._port2hub_connected.clear()
            self._port_free.clear()
        return
    
    @property
    def measure_distance_start(self) -> (datetime, DEV_VALUE):
        self._measure_distance_start = (datetime.now(), self._current_value)
        return self._measure_distance_start
    
    @property
    def measure_distance_end(self) -> (datetime, DEV_VALUE):
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE,
            wait: bool = False
            ) -> bool:
        async with self._port_free_condition:
            print(f"{self._name}.START_MOVE_DEGREES WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.START_MOVE_DEGREES PASSED THE GATES...")
            current_command = CMD_START_MOVE_DEV_DEGREES(
                synced=False,
                port=self._port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                degrees=degrees,
                speed=speed,
                abs_max_power=abs_max_power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_decc_profile=use_decc_profile)
            
            print(f"{self._name}.START_MOVE_DEGREES SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            print(f"{self._name}.START_MOVE_DEGREES SENDING COMPLETE...")
        return s
    
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE,
            wait: bool = False) -> bool:
        async with self._port_free_condition:
            print(f"{self._name}.START_SPEED_TIME WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.START_SPEED_TIME PASSED THE GATES...")
            current_command = CMD_START_MOVE_DEV_TIME(
                port=self._port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                time=time,
                speed=speed,
                direction=direction,
                power=power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_decc_profile=use_decc_profile)
            
            print(f"{self._name}.START_SPEED_TIME SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            print(f"{self._name}.START_SPEED_TIME SENDING COMPLETE...")
        return s
    
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
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE,
            ) -> bool:
        async with self._port_free_condition:
            print(f"{self._name}.GOTO_ABS_POS WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.GOTO_ABS_POS PASSED THE GATES...")
            current_command = CMD_MOVE_DEV_ABS_POS(
                synced=False,
                port=self._port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed=speed,
                abs_pos=abs_pos,
                abs_max_power=abs_max_power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_decc_profile=use_decc_profile)
            
            print(f"{self._name}.GOTO_ABS_POS SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
           
            self._port_free_condition.notify_all()
            print(f"{self._name}.GOTO_ABS_POS SENDING COMPLETE...")
        return s
    
    async def START_SPEED(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed_ccw: int = None,
            speed_cw: int = None,
            abs_max_power: int = 0,
            profile_nr: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE,
            ) -> bool:
        async with self._port_free_condition:
            print(f"{self._name}.START_SPEED WAITING AT THE GATES...")
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.START_SPEED PASSED THE GATES...")
            current_command = CMD_START_MOVE_DEV(
                synced=False,
                port=self._port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed_ccw=speed_ccw,
                speed_cw=speed_cw,
                abs_max_power=abs_max_power,
                profile_nr=profile_nr,
                use_acc_profile=use_acc_profile,
                use_decc_profile=use_decc_profile)

            print(f"{self._name}.START_SPEED SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            print(f"{self._name}.START_SPEED DONE...")
        return s
    
    @property
    def cmd_feedback_notification_str(self) -> str:
        return self._current_cmd_feedback_notification.m_cmd_feedback_str
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._current_cmd_feedback_notification
    
    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        if notification.m_cmd_feedback != CMD_FEEDBACK_MSG.MSG.EMPTY_BUF_CMD_IN_PROGRESS:
            self._port_free.set()
        else:
            self._port_free.clear()
        
        self._command_feedback_log.append(notification.m_cmd_feedback)
        self._current_cmd_feedback_notification = notification
        return
    
    @property
    def command_feedback_log(self) -> [CMD_FEEDBACK_MSG]:
        return self._command_feedback_log
    
    @command_feedback_log.setter
    def command_feedback_log(self, feedback: CMD_FEEDBACK_MSG) -> [CMD_FEEDBACK_MSG]:
        self._command_feedback_log.append(feedback)
        return
