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
from asyncio import Condition, Event
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime
from typing import List, Optional, Tuple, Union

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_GOTO_ABS_POS_DEV, CMD_START_MOVE_DEV_DEGREES, CMD_START_MOVE_DEV_TIME, CMD_TURN_SPEED_DEV, DOWNSTREAM_MESSAGE,
    )
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK, PORT_VALUE,
    )
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG, MOVEMENT, PERIPHERAL_EVENT, PORT, bcolors


class SingleMotor(AMotor):
    """Objects from this class represent a single Lego Motor.
    
    """
    
    def __init__(self,
                 server: [str, int],
                 port: bytes,
                 name: str = 'SingleMotor',
                 gearRatio: float = 1.0,
                 debug: bool = False
                 ):
        """
        This object models a single motor at a certain port.

        :param tuple[str,int] server: Tuple with (Host, Port) Information, e.g., ('127.0.0.1', 8888).
        :param Union[PORT, bytes] port: The port, e.g., b'\x02' of the SingleMotor (LegoBTLE.Constants.Port can be utilised).
        :param str name: A friendly name of the this Motor Device, e.g., 'FORWARD_MOTOR'.
        
        :param float gearRatio: The ratio of the number of teeth of the turning gear to the number of teeth of the
            turned gear.
            
        :param bool debug: Turn on/off debug Output.
        """

        self._error: Event = Event()
        self._error.clear()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_disconnected.set()
        self._hub_alert: Event = Event()
        self._hub_alert.clear()
        self._name: str = name
        self._port: bytes = port
        
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.clear()
        
        self._last_cmd_snt: Optional[DOWNSTREAM_MESSAGE] = None
        self._last_cmd_failed: Optional[DOWNSTREAM_MESSAGE] = None
        
        self._current_cmd_feedback_notification: Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: Optional[str] = None
        self._cmd_feedback_log: List[Tuple[float, CMD_FEEDBACK_MSG]] = []
        
        self._server: [str, int] = server
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: List[Tuple[float, EXT_SERVER_NOTIFICATION]] = []
        self._connection: [StreamReader, StreamWriter] = (..., ...)
        
        self._port_notification: Optional[DEV_PORT_NOTIFICATION] = None
        self._port2hub_connected: Event = Event()
        self._port2hub_connected.clear()
        
        self._gearRatio: [float, float] = (gearRatio, gearRatio)
        self._current_value: Optional[PORT_VALUE] = None
        self._last_value: Optional[PORT_VALUE] = None
        
        self._measure_distance_start = None
        self._measure_distance_end = None
        self._abs_max_distance = None
        
        self._error_notification: Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._error_notification_log: List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]] = []
        
        self._hub_action_notification: Optional[HUB_ACTION_NOTIFICATION] = None
        self._hub_attached_io_notification: Optional[HUB_ATTACHED_IO_NOTIFICATION] = None
        self._hub_alert_notification: Optional[HUB_ALERT_NOTIFICATION] = None
        self._hub_alert_notification_log: List[Tuple[float, HUB_ALERT_NOTIFICATION]] = []
        
        self._debug: bool = debug
        return
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str) -> None:
        """Sets a new friendly name.
        
        :param str name: The name.
        :return: Setter, nothing.
        :rtype: None
        
        """
        self._name = str(name)
        return
    
    @property
    def port(self) -> bytes:
        return self._port
    
    @port.setter
    def port(self, port: bytes) -> None:
        """Sets a new Lego(c)-Hub-Port.
        
        :param bytes port: The new port.
        :returns: Setter, nothing.
        :rtype: None
        
        """
        self._port = port
        return
    
    @property
    def port2hub_connected(self) -> Event:
        return self._port2hub_connected
    
    @property
    def port_value(self) -> PORT_VALUE:
        return self._current_value
    
    async def port_value_set(self, value: PORT_VALUE) -> None:
        """
        
        :param PORT_VALUE value: The device value to set.
        :return: Setter, nothing.
        :rtype: None
        """
        self._last_value = self._current_value
        self._current_value = value
        
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
    
    async def port_notification_set(self, notification: DEV_PORT_NOTIFICATION) -> None:
        if notification.m_status == PERIPHERAL_EVENT.IO_ATTACHED:
            self._port_free.set()
            self.port2hub_connected.set()
        elif notification.m_status == PERIPHERAL_EVENT.IO_DETACHED:
            self._port_free.clear()
            self.port2hub_connected.clear()
        self._port_notification = notification
        return
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @server.setter
    def server(self, server: Tuple[int, str]) -> None:
        """
        Sets new Server information.
        
        :param tuple[int, str] server: The host and port of the server.
        :return: None
        """
        self._server = server
    
    @property
    def connection(self) -> Tuple[StreamReader, StreamWriter]:
        return self._connection
    
    def connection_set(self, connection: Tuple[StreamReader, StreamWriter]) -> None:
        """
        Sets a new Server <-> Device Read/write connection.
        
        :param connection: The connection.
        :return: None
        """
        self._ext_srv_connected.set()
        self._connection = connection
        return
    
    @property
    def hub_alert(self) -> Event:
        return self._hub_alert
    
    @property
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        return self._hub_alert_notification
    
    async def hub_alert_notification_set(self, notification: HUB_ALERT_NOTIFICATION) -> None:
        self._hub_alert_notification = notification
        self._hub_alert.set()
        self._hub_alert_notification_log.append((datetime.timestamp(datetime.now()), notification))
        return
    
    @property
    def hub_alert_notification_log(self) -> List[Tuple[float, HUB_ALERT_NOTIFICATION]]:
        return self._hub_alert_notification_log
    
    @property
    def error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._error_notification
    
    async def error_notification_set(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._error_notification = error
        self._error.set()
        self._error_notification_log.append((datetime.timestamp(datetime.now()), error))
        return
    
    @property
    def error_notification_log(self) -> List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]]:
        return self._error_notification_log
    
    @property
    def gearRatio(self) -> [float, float]:
        return self._gearRatio
    
    @gearRatio.setter
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0) -> None:
        self._gearRatio = (gearRatio_motor_a, gearRatio_motor_b)
        return
    
    @property
    def ext_srv_connected(self) -> Event:
        return self._ext_srv_connected

    @property
    def ext_srv_disconnected(self) -> Event:
        return self._ext_srv_disconnected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification
    
    async def ext_srv_notification_set(self, notification: EXT_SERVER_NOTIFICATION):
        if notification is not None:
            self._ext_srv_notification = notification
            if self._debug:
                self._ext_srv_notification_log.append((datetime.timestamp(datetime.now()), notification))
            
            if self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED:
                self._ext_srv_connected.set()
                self._ext_srv_disconnected.clear()
                self.port2hub_connected.set()
            elif self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED:
                self._connection[1].close()
                self._port_free.clear()
                self._ext_srv_connected.clear()
                self._ext_srv_disconnected.set()
                self.port2hub_connected.clear()
                
                
        return
    
    @property
    def ext_srv_notification_log(self) -> List[Tuple[float, EXT_SERVER_NOTIFICATION]]:
        return self._ext_srv_notification_log
    
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
    
    async def hub_action_notification_set(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action_notification = action
        return
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io_notification
    
    async def hub_attached_io_notification_set(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        self._hub_attached_io_notification = io_notification
        if io_notification.m_io_event == PERIPHERAL_EVENT.IO_ATTACHED:
            print(f"MOTOR {self._name} is ATTACHED...")
            self.ext_srv_connected.set()
            self._ext_srv_disconnected.clear()
            self._port_free.set()
            self._port2hub_connected.set()
        elif io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED:
            print(f"MOTOR {self._name} is DETACHED...")
            self.ext_srv_connected.clear()
            self._ext_srv_disconnected.set()
            self._port_free.clear()
            self._port2hub_connected.clear()
        
        return
    
    @property
    def measure_start(self) -> Tuple[float, float]:
        self._measure_distance_start = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        return self._measure_distance_start
    
    @property
    def measure_end(self) -> Tuple[float, float]:
        self._measure_distance_end = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        """
        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfordegrees-degrees-speed-maxpower-endstate-useprofile-0x0b
        
        :param start_cond:
        :param completion_cond:
        :param degrees:
        :param speed:
        :param abs_max_power:
        :param on_completion:
        :param use_profile:
        :param use_acc_profile:
        :param use_decc_profile:
        :return: True if no errors in cmd_send occurred, False otherwise.
        """
        
        print(
            f"{bcolors.WARNING}{self._name}.START_MOVE_DEGREES {bcolors.UNDERLINE}{bcolors.BLINK}WAITING{bcolors.ENDC}"
            f" AT THE GATES...{bcolors.ENDC}")
        async with self._port_free_condition:
            await self._port_free.wait()
            self._port_free.clear()
            print(f"{self._name}.START_MOVE_DEGREES {bcolors.OKBLUE}PASSED{bcolors.ENDC} THE GATES...")
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
            print(f"{self._name}.START_MOVE_DEGREES SENDING COMPLETE...")
            self._port_free_condition.notify_all()
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
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        """
        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfortime-time-speed-maxpower-endstate-useprofile-0x09
        
        :param start_cond:
        :param completion_cond:
        :param time:
        :param speed:
        :param direction:
        :param power:
        :param on_completion:
        :param use_profile:
        :param use_acc_profile:
        :param use_decc_profile:
        :return: True if no errors in cmd_send occurred, False otherwise.
        """
        print(f"{self._name}.START_SPEED_TIME WAITING AT THE GATES...")
        async with self._port_free_condition:
            await self._port_free.wait()
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
            print(f"{self._name}.START_SPEED_TIME SENDING COMPLETE...")
            self._port_free_condition.notify_all()
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
            use_decc_profile=MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        """
        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos-speed-maxpower-endstate-useprofile-0x0d
        
        :param start_cond:
        :param completion_cond:
        :param speed:
        :param abs_pos:
        :param abs_max_power:
        :param on_completion:
        :param use_profile:
        :param use_acc_profile:
        :param use_decc_profile:
        :return: True if no errors in cmd_send occurred, False otherwise.
        """
        
        print(f"{self._name}.GOTO_ABS_POS WAITING AT THE GATES...")
        async with self._port_free_condition:
            await self._port_free.wait()
            self._port_free.clear()
            print(f"{self._name}.GOTO_ABS_POS PASSED THE GATES...")
            current_command = CMD_GOTO_ABS_POS_DEV(
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
            print(f"{self._name}.GOTO_ABS_POS SENDING COMPLETE...")
            self._port_free_condition.notify_all()
        return s
    
    async def START_SPEED(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed: int = None,
            abs_max_power: int = 0,
            profile_nr: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE, ) -> bool:
        """
        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07
        
        :param start_cond:
        :param completion_cond:
        :param speed:
        :param abs_max_power:
        :param profile_nr:
        :param use_acc_profile:
        :param use_decc_profile:
        :return: True if no errors in cmd_send occurred, False otherwise.
        """
        
        print(f"{self._name}.START_SPEED WAITING AT THE GATES...")
        async with self._port_free_condition:
            await self._port_free.wait()
            self._port_free.clear()
            print(f"{self._name}.START_SPEED PASSED THE GATES...")
            current_command = CMD_TURN_SPEED_DEV(
                    synced=False,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed=speed,
                    abs_max_power=abs_max_power,
                    profile_nr=profile_nr,
                    use_acc_profile=use_acc_profile,
                    use_decc_profile=use_decc_profile)
            
            print(f"{self._name}.START_SPEED SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            print(f"{self._name}.START_SPEED SENDING COMPLETE...")
            self._port_free_condition.notify_all()
        return s
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._current_cmd_feedback_notification
    
    async def cmd_feedback_notification_set(self, notification: PORT_CMD_FEEDBACK):
        print(f"{notification.m_port} PORT_CMD_FEEDBACK")
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x01', 'little'):
            print(f"RECEIVED CMD_STATUS: CMD STARTED {notification.COMMAND[len(notification.COMMAND) - 1]}")
            self._port_free.clear()
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x0a', 'little'):
            print(f"RECEIVED CMD_STATUS: CMD FINISHED {notification.COMMAND[len(notification.COMMAND) - 1]}")
            self._port_free.set()
        
        self._cmd_feedback_log.append((datetime.timestamp(datetime.now()), notification.m_cmd_status))
        self._current_cmd_feedback_notification = notification
        return
    
    # b'\x05\x00\x82\x10\x0a'
    
    @property
    def cmd_feedback_log(self) -> List[Tuple[float, CMD_FEEDBACK_MSG]]:
        return self._cmd_feedback_log
    
    @property
    def debug(self) -> bool:
        return self._debug
