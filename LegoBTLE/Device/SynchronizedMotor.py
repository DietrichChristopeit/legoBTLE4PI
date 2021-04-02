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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
import asyncio
import uuid
from asyncio import Event, Future, sleep
from asyncio.locks import Condition
from asyncio.streams import StreamReader, StreamWriter
from collections import defaultdict
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_GOTO_ABS_POS_DEV, CMD_SETUP_DEV_VIRTUAL_PORT, CMD_START_MOVE_DEV_DEGREES, CMD_START_MOVE_DEV_TIME,
    CMD_START_PWR_DEV, CMD_START_SPEED_DEV, DOWNSTREAM_MESSAGE,
)
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK, PORT_VALUE,
)
from LegoBTLE.LegoWP.types import (
    ALERT_STATUS, CMD_FEEDBACK_MSG, CONNECTION, MOVEMENT, PERIPHERAL_EVENT, PORT,
    bcolors,
)


class SynchronizedMotor(AMotor):
    """This class models the user view of two motors chained together on a common port.
    
    The available commands are executed in synchronized manner, so that the motors run in parallel and at
    least start at the same point in time.
    
    .. seealso:: https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-value-combinedmode
    
    """

    def __init__(self,
                 motor_a: AMotor,
                 motor_b: AMotor,
                 server: Tuple[str, int],
                 name: str = 'SynchronizedMotor',
                 debug: bool = False):
        """Initialize the Synchronized Motor.
         
         :param name: The combined motor's friendly name.
         :param motor_a: The first Motor instance.
         :param motor_b: The second Motor instance.
         :param server: The server to connect to as tuple('hostname', port)
         :param debug: Verbose info yes/no
         
         """
        self._id: str = uuid.uuid4().hex
        
        self._DEVNAME = ''.join(name.split(' '))
        
        self._current_cmd_feedback_notification: Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: Optional[str] = None
        self._cmd_feedback_log: List[Tuple[float, CMD_FEEDBACK_MSG]] = []
        
        self._hub_alert_notification: Optional[HUB_ALERT_NOTIFICATION] = None
        self._hub_alert_notification_log: List[Tuple[float, HUB_ALERT_NOTIFICATION]] = []
        self._hub_action = None
        self._hub_attached_io = None
        self._hub_alert: Event = Event()
        self._hub_alert.clear()
        
        self._name = name
        
        self._port = motor_a.port + motor_b.port
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        if motor_a.port_free.is_set() and motor_b.port_free.is_set():
            self._port_free.set()
        else:
            self._port_free.clear()
        self._port_connected: Event = Event()
        self._port_connected.clear()
        
        self._server = server
        self._connection: [StreamReader, StreamWriter] = (..., ...)
        
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: List[Tuple[float, EXT_SERVER_NOTIFICATION]] = []
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_disconnected.set()
        
        self._motor_a: AMotor = motor_a
        self._gearRatio: Tuple[float, float] = (1.0, 1.0)
        self._wheeldiameter: Tuple[float, float] = (100.0, 100.0)
        self._motor_a_port: bytes = motor_a.port
        self._motor_b: AMotor = motor_b
        self._motor_b_port: bytes = motor_b.port
        
        self._current_value = None
        self._last_value = None
        self._measure_distance_start = None
        self._measure_distance_end = None
        
        self._error_notification: Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._error_notification_log: List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]] = []
        
        self._cmd_status = None
        self._last_cmd_snt = None
        self._last_cmd_failed = None
        
        self._acc_deacc_profiles: defaultdict = defaultdict(defaultdict)
        self._current_profile: defaultdict = defaultdict(None)

        self._E_MOTOR_STALLED: Event = Event()
        self._debug = debug
        return
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def DEVNAME(self) -> str:
        return self._DEVNAME
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str):
        self._name = name
        return
    
    @property
    def E_MOTOR_STALLED(self) -> Event:
        return self._E_MOTOR_STALLED
    
    @property
    def wheelDiameter(self) -> float:
        raise NotImplementedError
    
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
    
    async def ext_srv_notification_set(self, notification: EXT_SERVER_NOTIFICATION):
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
    def ext_srv_notification_log(self) -> List[Tuple[float, EXT_SERVER_NOTIFICATION]]:
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
    def gearRatio(self) -> Tuple[float, float]:
        return self._gearRatio
    
    @gearRatio.setter
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0):
        self._gearRatio = (gearRatio_motor_a, gearRatio_motor_b)
        return
    
    @property
    def wheel_diameter(self) -> Tuple[float, float]:
        return self._wheeldiameter
    
    @wheel_diameter.setter
    def wheel_diameter(self, diameter_a: float = 100.0, diameter_b: float = 100.0):
        """

        Keyword Args:
            diameter_a (float): The wheel diameter of wheels attached to the first motor in mm.
            diameter_b (float): The wheel diameter of wheels attached to the second motor in mm.

        Returns:
            nothing (None):
        """
        self._wheeldiameter = (diameter_a, diameter_b)
        return

    @property
    def total_distance(self) -> float:
        return 1.0

    @property
    def distance(self) -> float:
        return 1.0
    
    @property
    def measure_start(self) -> Tuple[float, float]:
        self._measure_distance_start = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        return self._measure_distance_start
    
    @property
    def measure_end(self) -> Tuple[float, float]:
        self._measure_distance_end = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        return self._measure_distance_end
    
    async def VIRTUAL_PORT_SETUP(self, connect: bool = True, result: Future = None):
        """

        Parameters
        ----------
        connect : bool
            If True request a virtual port number, False disconnect the virtual port.
        result :

        Returns
        -------

        """
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            if connect:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connection=CONNECTION.CONNECT,
                        port_a=PORT(self._motor_a_port),
                        port_b=PORT(self._motor_b_port), )
            else:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connection=CONNECTION.DISCONNECT,
                        port=self._port, )
            
            s = await self.cmd_send(current_command)
            self._port_free_condition.notify_all()
        result.set_result(s)
        return
    
    async def START_SPEED_UNREGULATED_SYNCED(
            self,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed_a: int = None,
            direction_a: int = MOVEMENT.FORWARD,
            speed_b: int = None,
            direction_b: int = MOVEMENT.FORWARD,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: int = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = 1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """

        Parameters
        ----------
        start_cond :
        completion_cond :
        speed_a :
        direction_a :
        speed_b :
        direction_b :
        use_profile :
        use_acc_profile :
        use_deacc_profile :
        time_to_stalled :
        result :
        waitUntil :
        waitUntil_timeout :
        delay_before :
        delay_after :

        Returns
        -------

        """
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
    
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
            current_command = CMD_START_SPEED_DEV(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed_a=speed_a,
                    direction_a=direction_a,
                    speed_b=speed_b,
                    direction_b=direction_b,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile,
                    )
            print(
                    f"{self._name}.START_SPEED {bcolors.WARNING}{bcolors.BLINK}SENDING "
                    f"{current_command.COMMAND.hex()}{bcolors.ENDC}...")
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            print(
                    f"{self._name}.START_SPEED SENDING {bcolors.OKBLUE}COMPLETE{current_command.COMMAND.hex()}..."
                    f"{bcolors.ENDC}")
    
            if delay_after is not None:
                if self.debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
    
            # _wait_until part
            if waitUntil is not None:
                fut = Future()
                await self._wait_until(waitUntil, fut)
                done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
            self.port_free_condition.notify_all()
        result.set_result(s)
        return
    
    async def START_POWER_UNREGULATED_SYNCED(self,
                                             power_a: int = None,
                                             direction_a: int = MOVEMENT.FORWARD,
                                             power_b: int = None,
                                             direction_b: int = MOVEMENT.FORWARD,
                                             use_profile: int = None,
                                             use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
                                             use_decc_profile: int = MOVEMENT.USE_DEC_PROFILE,
                                             start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                             time_to_stalled: float = 1.0,
                                             result: Future = None,
                                             wait_condition: Callable = None,
                                             wait_timeout: float = None,
                                             delay_before: float = None,
                                             delay_after: float = None,
                                             ):
        """
        
        Keyword Args:
            power_a (int):
            direction_a (int):
            power_b (int):
            direction_b (int):
            use_profile ():
            use_acc_profile ():
            use_decc_profile ():
            start_cond ():
            result ():

        Returns:

        """
        
        if self._debug:
            print(
                    f"{bcolors.WARNING}{self._name}.START_POWER_UNREGULATED AT THE GATES...{bcolors.ENDC}"
                    f"{bcolors.UNDERLINE}{bcolors.OKBLUE}WAITING {bcolors.ENDC}")
        
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            self._port_free.clear()
    
            if self._debug:
                print(f"{self._name}.START_POWER_UNREGULATED {bcolors.OKBLUE}PASSED{bcolors.ENDC} THE GATES...")
    
            if delay_before is not None:
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
            current_command = CMD_START_PWR_DEV(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                    power_a=power_a,
                    direction_a=direction_a,
                    power_b=power_b,
                    direction_b=direction_b,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_decc_profile,
                    )
    
            if self._debug:
                print(f"{self._name}.START_POWER_UNREGULATED SENDING {current_command.COMMAND.hex()}...")
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self._debug:
                print(f"{self._name}.START_POWER_UNREGULATED SENDING COMPLETE...")
    
            if delay_after is not None:
                if self.debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
    
            # _wait_until part
            if wait_condition is not None:
                fut = Future()
                await self._wait_until(wait_condition, fut)
                done, pending = await asyncio.wait((fut,), timeout=wait_timeout)
            self._port_free_condition.notify_all()
        result.set_result(s)
        return
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise UserWarning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    async def port_notification_set(self, notification: DEV_PORT_NOTIFICATION):
        raise UserWarning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @property
    def port_value(self) -> PORT_VALUE:
        return self._current_value
    
    async def port_value_set(self, new_value: PORT_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return

    @property
    def last_value(self) -> PORT_VALUE:
        return self._last_value
    
    @property
    def error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        return self._error_notification
    
    async def error_notification_set(self, error: DEV_GENERIC_ERROR_NOTIFICATION):
        self._error_notification = error
        self._error_notification_log.append((datetime.timestamp(datetime.now()), error))
        return
    
    @property
    def error_notification_log(self) -> List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]]:
        return self._error_notification_log
    
    @property
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        return self._hub_action
    
    async def hub_action_notification_set(self, action: HUB_ACTION_NOTIFICATION):
        self._hub_action = action
        return
    
    @property
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        return self._hub_attached_io
    
    def hub_attached_io_notification_set(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        if io_notification.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED:
            self._port_connected.set()
            self._port_free.set()
            self._motor_a.port_free.set()
            self._motor_b.port_free.set()
        elif io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED:
            self._port_connected.clear()
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
        self._hub_attached_io = io_notification
        self._port = io_notification.m_port
        self._motor_a_port = io_notification.m_vport_a
        self._motor_b_port = io_notification.m_vport_b
        return
    
    @property
    def last_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        return self._last_cmd_snt
    
    @last_cmd_snt.setter
    def last_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        self._last_cmd_snt = command
        return
    
    @property
    def current_profile(self) -> defaultdict:
        return self._current_profile
    
    @current_profile.setter
    def current_profile(self, profile: defaultdict):
        self._current_profile = profile
        return
    
    @property
    def acc_dec_profiles(self) -> defaultdict:
        return self._acc_deacc_profiles
    
    @acc_deacc_profiles.setter
    def acc_dec_profiles(self, profiles: defaultdict):
        self._acc_deacc_profiles = profiles
        return
    
    async def START_MOVE_DEGREES_SYNCED(
            self,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed_a: int = None,
            speed_b: int = None,
            abs_max_power: int = 0,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: int = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = 1.0,
            result: Future = None,
            wait_condition: Callable = None,
            wait_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        print(
                f"{bcolors.WARNING}{self._name}.START_MOVE_DEGREES AT THE GATES... {bcolors.ENDC}"
                f"{bcolors.OKBLUE}{bcolors.UNDERLINE}WAITING {bcolors.ENDC}")
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            if self._debug:
                print(f"{bcolors.WARNING}{self._name}.START_POWER_UNREGULATED THE GATES... {bcolors.ENDC}"
                      f"{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED {bcolors.ENDC}")
    
            if delay_before is not None:
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
            current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    degrees=int(round(round(degrees * self.gearRatio[0]) + round(degrees * self.gearRatio[1]) / 2)), # not really ok, needs better thinking
                    speed_a=speed_a,
                    speed_b=speed_b,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile, )
            print(
                    f"{self._name}.START_MOVE_DEGREES {bcolors.WARNING}{bcolors.BLINK}SENDING "
                    f"{current_command.COMMAND.hex()}{bcolors.ENDC}...")
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
    
            s = await self.cmd_send(current_command)
            if self._debug:
                print(
                        f"{self._name}.START_MOVE_DEGREES SENDING {bcolors.OKBLUE}COMPLETE"
                        f"{current_command.COMMAND.hex()}..."
                        f"{bcolors.ENDC}")
    
            if delay_after is not None:
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
    
            # _wait_until part
            if wait_condition is not None:
                fut = Future()
                await self._wait_until(wait_condition, fut)
                done, pending = await asyncio.wait((fut,), timeout=wait_timeout)
            self._port_free_condition.notify_all()
        result.set_result(s)
        return
    
    async def START_SPEED_TIME_SYNCED(
            self,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            time: int = 0,
            speed_a: int = None,
            direction_a: int = MOVEMENT.FORWARD,
            speed_b: int = None,
            direction_b: int = MOVEMENT.FORWARD,
            power: int = 0,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: int = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = 1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """

        Parameters
        ----------
        start_cond :
        completion_cond :
        time :
        speed_a :
        direction_a :
        speed_b :
        direction_b :
        power :
        on_completion :
        use_profile :
        use_acc_profile :
        use_deacc_profile :
        time_to_stalled :
        result :
        waitUntil :
        waitUntil_timeout :
        delay_before :
        delay_after :

        Returns
        -------

        """
        if self._debug:
            print(
                f"{self._name}.START_SPEED_TIME {bcolors.WARNING}{bcolors.BLINK}WAITING AT THE GATES{bcolors.ENDC}...")
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            if self._debug:
                print(
                        f"{self._name}.START_SPEED_TIME {bcolors.OKBLUE}{bcolors.BLINK}RECEIVED PORT_FREE{bcolors.ENDC}...")
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
    
            if delay_before is not None:
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
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
                    use_deacc_profile=use_deacc_profile, )
            print(
                    f"{self._name}.START_SPEED_TIME {bcolors.WARNING}{bcolors.BLINK}SENDING "
                    f"{current_command.COMMAND.hex()}{bcolors.ENDC}...")
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
    
            s = await self.cmd_send(current_command)
            if self._debug:
                print(
                        f"{self._name}.START_SPEED_TIME SENDING {bcolors.OKBLUE}COMPLETE"
                        f"{current_command.COMMAND.hex()}...{bcolors.ENDC}")
    
            if delay_after is not None:
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
    
            # _wait_until part
            if waitUntil is not None:
                fut = Future()
                await self._wait_until(waitUntil, fut)
                done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
            self._port_free_condition.notify_all()
        result.set_result(s)
        return
    
    async def GOTO_ABS_POS_SYNCED(
            self,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed: int = 0,
            abs_pos_a: int = None,
            abs_pos_b: int = None,
            abs_max_power: int = 0,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: int = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = 1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        
        print(
                f"{self._name}.GOTO_ABS_POS {bcolors.WARNING}{bcolors.BLINK}WAITING AT THE GATES{bcolors.ENDC}...")
        async with self._port_free_condition:
            await self._ext_srv_connected.wait()
            await self._port_free.wait()
            print(
                    f"{self._name}.GOTO_ABS_POS {bcolors.OKBLUE}{bcolors.BLINK}RECEIVED PORT_FREE{bcolors.ENDC}...")
            self._port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
    
            if delay_before is not None:
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self._debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
            current_command = CMD_GOTO_ABS_POS_DEV(
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
                    use_deacc_profile=use_deacc_profile,
                    )
            print(
                    f"{self._name}.GOTO_ABS_POS {bcolors.WARNING}{bcolors.BLINK}SENDING "
                    f"{current_command.COMMAND.hex()}{bcolors.ENDC}...")
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
    
            s = await self.cmd_send(current_command)
            print(
                    f"{self._name}.GOTO_ABS_POS SENDING {bcolors.OKBLUE}COMPLETE{current_command.COMMAND.hex()}..."
                    f"{bcolors.ENDC}")
    
            if delay_after is not None:
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self._debug:
                    print(f"DELAY_AFTER / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKGREEN}DONE{bcolors.ENDC}"
                          )
    
    
            # _wait_until part
            if waitUntil is not None:
                fut = Future()
                await self._wait_until(waitUntil, fut)
                done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
            self._port_free_condition.notify_all()
        result.set_result(s)
        return
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._current_cmd_feedback_notification
    
    async def cmd_feedback_notification_set(self, notification: PORT_CMD_FEEDBACK):
        fb: bool = True
        
        for port in notification.m_port:
            if notification.m_cmd_status[port].MSG.EMPTY_BUF_CMD_IN_PROGRESS:
                fb = False
                break
        if fb:
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
    def cmd_feedback_log(self) -> List[Tuple[float, CMD_FEEDBACK_MSG]]:
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
    
    def connection_set(self, connection: Tuple[asyncio.StreamReader, asyncio.StreamWriter]) -> None:
        self._ext_srv_connected.set()
        self._connection = connection
        return
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @property
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        return self._hub_alert_notification
    
    async def hub_alert_notification_set(self, notification: HUB_ALERT_NOTIFICATION):
        self._hub_alert_notification = notification
        self._hub_alert_notification_log.append((datetime.timestamp(datetime.now()), notification))
        self._hub_alert.set()
        if notification.hub_alert_status == ALERT_STATUS.ALERT:
            raise ResourceWarning(f"Hub Alert Received: {notification.hub_alert_type_str}")
        return
    
    @property
    def hub_alert_notification_log(self) -> List[Tuple[float, HUB_ALERT_NOTIFICATION]]:
        return self._hub_alert_notification_log
    
    @property
    def debug(self) -> bool:
        return self._debug
