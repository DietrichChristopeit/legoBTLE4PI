# coding=utf-8
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
import typing
from asyncio import Event
from asyncio.locks import Condition
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_MOVE_DEV_ABS_POS, CMD_SETUP_DEV_VIRTUAL_PORT, CMD_START_MOVE_DEV, CMD_START_MOVE_DEV_DEGREES,
    CMD_START_MOVE_DEV_TIME, DOWNSTREAM_MESSAGE,
    )
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, DEV_VALUE, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION,
    HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK,
    )
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG, CONNECTION_STATUS, MOVEMENT, PERIPHERAL_EVENT, PORT


class SynchronizedMotor(AMotor):
    """This class models the user view of two motors chained together on a common port.
    
    The available commands are executed in synchronized manner, so that the motors run in parallel and at
    least start at the same point in time.
    
    See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-value-combinedmode
    
    """

    def __init__(self,
                 motor_a: AMotor,
                 motor_b: AMotor,
                 server: tuple[str, int],
                 name: str = 'SynchronizedMotor',
                 debug: bool = False):
        """Initialize the Synchronized Motor.
         
         :param name: The combined motor's friendly name.
         :param motor_a: The first Motor instance.
         :param motor_b: The second Motor instance.
         :param server: The server to connect to as tuple('hostname', port)
         :param debug: Verbose info yes/no
         
         """

        self._current_cmd_feedback_notification: typing.Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: typing.Optional[str] = None
        self._cmd_feedback_log: [CMD_FEEDBACK_MSG] = []
        
        self._hub_alert_notification: typing.Optional[HUB_ALERT_NOTIFICATION] = None
        self._hub_alert_notification_log: [(datetime, HUB_ALERT_NOTIFICATION)] = []
        
        self._name = name
        
        self._port = None
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        if motor_a.port_free.is_set() and motor_b.port_free.is_set():
            self.port_free.set()
        else:
            self.port_free.clear()
        self._port_connected: Event = Event()
        self._port_connected.clear()
        
        self._server = server
        self._connection: [StreamReader, StreamWriter] = (..., ...)
        
        self._ext_srv_notification: typing.Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: [(datetime, EXT_SERVER_NOTIFICATION)] = []
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_connected.set()
        
        self._motor_a: AMotor = motor_a
        self._gearRatio: {float, float} = {1.0, 1.0}
        self._motor_a_port: bytes = motor_a.port
        self._motor_b: AMotor = motor_b
        self._motor_b_port: bytes = motor_b.port
        
        self._current_value = None
        self._last_value = None
        self._measure_distance_start = None
        self._measure_distance_end = None
        
        self._error_notification: typing.Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._error_notification_log: [(datetime, DEV_GENERIC_ERROR_NOTIFICATION)] = []
        
        self._hub_action = None
        self._hub_attached_io = None
        
        self._cmd_status = None
        self._last_cmd_snt = None
        self._last_cmd_failed = None
        
        self._debug = debug
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
    def port_free(self) -> Event:
        return self._port_free
    
    @property
    def port2hub_connected(self) -> Event:
        return self._port_connected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, notification: EXT_SERVER_NOTIFICATION):
        if notification is not None:
            self._ext_srv_notification = notification
            if self._debug:
                self._ext_srv_notification_log.append((datetime.timestamp(datetime.now()), notification))
            if notification.m_event_str != 'EXT_SRV_CONNECTED':
                self._ext_srv_connected.set()
                self._ext_srv_disconnected.clear()
            else:
                self._ext_srv_connected.clear()
                self._ext_srv_disconnected.set()
        return
    
    @property
    def ext_srv_notification_log(self) -> [(datetime, EXT_SERVER_NOTIFICATION)]:
        return self._ext_srv_notification_log
    
    @property
    def ext_srv_connected(self) -> Event:
        return self._ext_srv_connected
    
    @property
    def ext_srv_disconnected(self) -> Event:
        return self._ext_srv_disconnected
    
    @property
    def first_motor(self) -> AMotor:
        return self._motor_a
    
    @property
    def first_motor_port(self) -> bytes:
        return PORT(self._motor_a_port).value
    
    @property
    def second_motor(self) -> AMotor:
        return self._motor_b
    
    @property
    def second_motor_port(self) -> bytes:
        return PORT(self._motor_b_port).value
    
    @property
    def gearRatio(self) -> {float, float}:
        return {self._gearRatio, self._gearRatio}
    
    @gearRatio.setter
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0):
        self._gearRatio = {gearRatio_motor_a, gearRatio_motor_b}
        return
    
    @property
    def measure_distance_start(self) -> (datetime, DEV_VALUE):
        self._measure_distance_start = (datetime.timestamp(datetime.now()), self._current_value)
        return self._measure_distance_start
    
    @property
    def measure_distance_end(self) -> (datetime, DEV_VALUE):
        self._measure_distance_end = (datetime.timestamp(datetime.now()), self._current_value)
        return self._measure_distance_end
    
    async def VIRTUAL_PORT_SETUP(self, connect: bool = True, ) -> bool:
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set() and
                                                             self._motor_b.port_free.is_set())
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            if connect:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connectionType=CONNECTION_STATUS.CONNECT,
                        port_a=PORT(self._motor_a_port).value,
                        port_b=PORT(self._motor_b_port).value, )
            else:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connectionType=CONNECTION_STATUS.DISCONNECT,
                        port=self._port, )
            
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            return s
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise UserWarning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        raise UserWarning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @property
    def port_value(self) -> DEV_VALUE:
        return self._current_value
    
    @port_value.setter
    def port_value(self, new_value: DEV_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return
    
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
        return self._hub_action
    
    @hub_action_notification.setter
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action = action
        return
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io
    
    @hub_attached_io_notification.setter
    def hub_attached_io_notification(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        if io_notification.m_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED:
            self._port_connected.set()
        elif io_notification.m_event == PERIPHERAL_EVENT.IO_DETACHED:
            self._port_connected.clear()
        self._hub_attached_io = io_notification
        self._port = io_notification.m_port
        self._motor_a_port = PORT(io_notification.m_vport_a)
        self._motor_b_port = PORT(io_notification.m_vport_b)
        return
    
    @property
    def last_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        return self._last_cmd_snt
    
    @last_cmd_snt.setter
    def last_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        self._last_cmd_snt = command
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set() and
                                                             self._motor_b.port_free.is_set())
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    degrees=degrees,
                    speed_a=speed_a,
                    speed_b=speed_b,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_decc_profile=use_decc_profile, )
            
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            return s
    
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set() and
                                                             self._motor_b.port_free.is_set())
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            current_command = CMD_START_MOVE_DEV_TIME(
                    port=self._port,
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
                    use_decc_profile=use_decc_profile, )
            
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            return s
    
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
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set() and
                                                             self._motor_b.port_free.is_set())
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            current_command = CMD_MOVE_DEV_ABS_POS(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed=speed,
                    abs_pos_a=abs_pos_a,
                    abs_pos_b=abs_pos_b,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_decc_profile=use_decc_profile, )
            
            s = await self.cmd_send(current_command)
            
            self._port_free_condition.notify_all()
            return s
    
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE,
            ) -> bool:
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set() and
                                                             self._motor_b.port_free.is_set())
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            current_command = CMD_START_MOVE_DEV(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed_ccw_1=speed_ccw_1,
                    speed_cw_1=speed_cw_1,
                    speed_ccw_2=speed_ccw_2,
                    speed_cw_2=speed_cw_2,
                    abs_max_power=abs_max_power,
                    profile_nr=profile_nr,
                    use_acc_profile=use_acc_profile,
                    use_decc_profile=use_decc_profile, )
            s = await self.cmd_send(current_command)
            self._port_free_condition.notify_all()
        return s
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._current_cmd_feedback_notification
    
    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        fbe: bool = True
        for fb in notification.m_cmd_feedback:
            if fb != CMD_FEEDBACK_MSG.MSG.EMPTY_BUF_CMD_IN_PROGRESS:
                fbe &= True
            else:
                fbe = False
        if fbe:
            self._port_free.set()
            self._motor_a.port_free.set()
            self._motor_b.port_free.set()
        else:
            
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
        
        self._current_cmd_feedback_notification = notification
        return
    
    @property
    def cmd_feedback_log(self) -> list[CMD_FEEDBACK_MSG]:
        return self._cmd_feedback_log
    
    @property
    def port_free_condition(self) -> Condition:
        return self._port_free_condition
    
    @property
    def last_cmd_failed(self) -> DOWNSTREAM_MESSAGE:
        return self._last_cmd_failed
    
    @property
    def connection(self) -> [StreamReader, StreamWriter]:
        return self._connection
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @property
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        return self._hub_alert_notification
    
    @hub_alert_notification.setter
    def hub_alert_notification(self, notification: HUB_ALERT_NOTIFICATION):
        self.hub_alert_notification = notification
        self._hub_alert_notification_log.append((datetime.timestamp(datetime.now()), notification))
        return

    @property
    def hub_alert_notification_log(self) -> [(datetime, HUB_ALERT_NOTIFICATION)]:
        return self._hub_alert_notification_log
    
    @property
    def debug(self) -> bool:
        return self._debug
