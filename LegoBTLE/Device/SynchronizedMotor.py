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
from asyncio import Event
from asyncio import sleep
from asyncio.locks import Condition
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter
from collections import defaultdict
from datetime import datetime
from time import monotonic
from typing import Awaitable
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import CMD_GOTO_ABS_POS_DEV
from LegoBTLE.LegoWP.messages.downstream import CMD_SETUP_DEV_VIRTUAL_PORT
from LegoBTLE.LegoWP.messages.downstream import CMD_START_MOVE_DEV_DEGREES
from LegoBTLE.LegoWP.messages.downstream import CMD_START_MOVE_DEV_TIME
from LegoBTLE.LegoWP.messages.downstream import CMD_START_PWR_DEV
from LegoBTLE.LegoWP.messages.downstream import CMD_START_SPEED_DEV
from LegoBTLE.LegoWP.messages.downstream import DOWNSTREAM_MESSAGE
from LegoBTLE.LegoWP.messages.upstream import DEV_GENERIC_ERROR_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import DEV_PORT_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import EXT_SERVER_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import HUB_ACTION_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import HUB_ALERT_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import HUB_ATTACHED_IO_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import PORT_CMD_FEEDBACK
from LegoBTLE.LegoWP.messages.upstream import PORT_VALUE
from LegoBTLE.LegoWP.types import ALERT_STATUS
from LegoBTLE.LegoWP.types import C
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG
from LegoBTLE.LegoWP.types import CONNECTION
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.LegoWP.types import PERIPHERAL_EVENT
from LegoBTLE.LegoWP.types import PORT
from LegoBTLE.networking.prettyprint.debug import debug_info
from LegoBTLE.networking.prettyprint.debug import debug_info_begin
from LegoBTLE.networking.prettyprint.debug import debug_info_end
from LegoBTLE.networking.prettyprint.debug import debug_info_footer
from LegoBTLE.networking.prettyprint.debug import debug_info_header


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
                 forward: MOVEMENT = MOVEMENT.FORWARD,
                 debug: bool = False):
        """Initialize the Synchronized Motor.
         
         
         
         :param name: The combined motor's friendly name.
         :param motor_a: The first Motor instance.
         :param motor_b: The second Motor instance.
         :param server: The server to connect to as tuple('hostname', port)
         :param debug: Verbose info yes/no
         
         """
    
        self._id: str = uuid.uuid4().hex
        self._synced: bool = True
    
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
    
        self._motor_a: AMotor = motor_a
        self._name = name
        self._motor_a_port: bytes = motor_a.port
        self._motor_b: AMotor = motor_b
        self._motor_b_port: bytes = motor_b.port
    
        self._port = int.to_bytes((110 +
                                   1 * int.from_bytes(motor_a.port, 'little', signed=False) +
                                   2 * int.from_bytes(motor_b.port, 'little', signed=False)),
                                  length=1,
                                  byteorder='little',
                                  signed=False)
    
        print(f"SYNCHRONIZED MOTOR CLASS: SETUP PORT {self._port[0]}")
        # initial, so that there's a value
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()
    
        self._command_end: Event = Event()
        self._command_end.set()
    
        self._port_connected: Event = Event()
        self._port2hub_connected: Event = Event()
    
        self._server = server
        self._connection: [StreamReader, StreamWriter] = (..., ...)
    
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: List[Tuple[float, EXT_SERVER_NOTIFICATION]] = []
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_disconnected.set()
    
        self._gearRatio: Tuple[float, float] = (1.0, 1.0)
        self._wheeldiameter: Tuple[float, float] = (100.0, 100.0)
    
        self._forward = forward
    
        self._forward_direction_a: MOVEMENT = self._motor_a.forward_direction
        self._clockwise_direction_a: MOVEMENT = self._motor_a.clockwise_direction
        self._forward_direction_b: MOVEMENT = self._motor_b.forward_direction
        self._clockwise_direction_b: MOVEMENT = self._motor_b.clockwise_direction
    
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
    def forward_direction(self) -> Tuple[MOVEMENT, MOVEMENT]:
        return self._motor_a.forward_direction, self._motor_b.forward_direction
    
    @property
    def clockwise_direction(self) -> Tuple[MOVEMENT, MOVEMENT]:
        return self._clockwise_direction_a, self._clockwise_direction_b
    
    @property
    def port(self) -> bytes:
        return self._port
    
    @port.setter
    def port(self, port: bytes):
        self._port = port
        return
    
    @property
    def synced(self) -> bool:
        return self._synced
    
    @property
    def command_end(self) -> Event:
        return self._command_end
    
    @property
    def port_free(self) -> Event:
        return self._port_free
    
    @property
    def port2hub_connected(self) -> Event:
        return self._port2hub_connected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        return self._ext_srv_notification
    
    async def ext_srv_notification_set(self, notification: EXT_SERVER_NOTIFICATION):
        debug_info_header(f"{self._name}: RECEIVED EXTERNAL_SERVER_NOTIFICATION ", debug=self._debug)
        debug_info(f"PORT: {self._port[0]}", debug=self._debug)
        if notification is not None:
            self._ext_srv_notification = notification
            if self._debug:
                self._ext_srv_notification_log.append((datetime.timestamp(datetime.now()), notification))
            if notification.m_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED:
                self._ext_srv_connected.set()
                self._ext_srv_disconnected.clear()
                self._port2hub_connected.set()
                self._port_free.set()
            
            elif notification.m_event == PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED:
                self._connection[1].close()
                self._port_free.clear()
                self._ext_srv_connected.clear()
                self._ext_srv_disconnected.set()
                self._port2hub_connected.clear()
            
            debug_info(f"EXT_SRV_CONNECTED?:    {self._ext_srv_connected.is_set()}", debug=self._debug)
            debug_info(f"EXT_SRV_DISCONNECTED?: {self._ext_srv_disconnected.is_set()}", debug=self._debug)
            debug_info(f"PORT2HUB_CONNECTED?:   {self._port2hub_connected.is_set()}", debug=self._debug)
            debug_info(f"PORT_FREE?:            {self._port_free.is_set()}", debug=self._debug)
            debug_info_footer(footer=f"{self._name}: RECEIVED EXTERNAL_SERVER_NOTIFICATION", debug=self._debug)
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
    
    async def VIRTUAL_PORT_SETUP(self, connect: bool = True):
        """

        Parameters
        ----------
        connect : bool
            If True request a virtual port number, False disconnect the virtual port.
            
        Returns
        -------

        """
        async with self._port_free_condition:
            print(f"IN VIRTUAL PORT SETUP... Waiting at the gates")
            await self._motor_a.ext_srv_connected.wait()
            await self._motor_b.ext_srv_connected.wait()
            # await self._port_free.wait()
            self._port_free.clear()
            # self._motor_a.port_free.clear()
            # self._motor_b.port_free.clear()
            print(f"IN VIRTUAL PORT SETUP... PASSED the gates")
            if connect:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connection=CONNECTION.CONNECT,
                        port_a=self._motor_a_port,
                        port_b=self._motor_b_port, )
            else:
                current_command = CMD_SETUP_DEV_VIRTUAL_PORT(
                        connection=CONNECTION.DISCONNECT,
                        port=self._port, )
            print(f"IN VIRTUAL PORT SETUP... SENDING")
            s = await self._cmd_send(current_command)
            self._port_free.set()
            self._port_free_condition.notify_all()
        print(f"IN VIRTUAL PORT SETUP... SENDING DONE")
        return s
    
    async def START_SPEED_UNREGULATED(self,
                                      speed: int,
                                      abs_max_power: int = 30,
                                      use_profile: int = 0,
                                      use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
                                      use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
                                      start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                      completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                                      on_stalled: Awaitable = None,
                                      time_to_stalled: float = 1.0,
                                      wait_cond: Callable = None,
                                      wait_cond_timeout: float = None,
                                      delay_before: float = None,
                                      delay_after: float = None,
                                      ):
        await self.START_SPEED_UNREGULATED_SYNCED(speed_a=speed,
                                                  speed_b=speed,
                                                  abs_max_power=abs_max_power,
                                                  use_profile=use_profile,
                                                  use_acc_profile=use_acc_profile,
                                                  use_dec_profile=use_dec_profile,
                                                  start_cond=start_cond,
                                                  completion_cond=completion_cond,
                                                  on_stalled=on_stalled,
                                                  time_to_stalled=time_to_stalled,
                                                  wait_cond=wait_cond,
                                                  wait_cond_timeout=wait_cond_timeout,
                                                  delay_before=delay_before,
                                                  delay_after=delay_after, )
        return
    
    async def START_SPEED_UNREGULATED_SYNCED(
            self,
            speed_a: int,
            speed_b: int,
            abs_max_power: int = 30,
            time_to_stalled: float = 1.0,
            on_stalled: Awaitable = None,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
            wait_cond: Callable = None,
            wait_cond_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """

        Parameters
        ----------
        
        on_stalled: Optional[Awaitable]
            Set a callback for when the Event `_E_MOTOR_STALLED` gets set.
        start_cond :
        completion_cond :
        speed_a :
        speed_b :
        use_profile :
        use_acc_profile :
        use_dec_profile :
        time_to_stalled :
        wait_cond :
        wait_cond_timeout :
        delay_before :
        delay_after :

        Returns
        -------

        """
        speed_a *= self._motor_a.forward_direction  # normalize speed
        speed_b *= self._motor_b.forward_direction  # normalize speed
        
        debug_info_header(f"NAME: {self.name} / PORT: {self.port[0]} # START_POWER_UNREGULATED_SYNCED", debug=self.debug)
        debug_info_begin(
                f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # WAITING AT THE GATES",
                debug=self.debug)
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            debug_info_end(f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # PASSED THE GATES",
                           debug=self.debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
            
            current_command = CMD_START_SPEED_DEV(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed_a=speed_a,
                    speed_b=speed_b,
                    abs_max_power=abs_max_power,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile,
                    )
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # sending CMD", debug=self.debug)
            # _wait_until part
            if wait_cond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(wait_cond, fut)
                done = await asyncio.wait_for(fut, timeout=wait_cond_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            # stalled condition part
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self._cmd_send(current_command)
            debug_info(f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # CMD: {current_command}",
                       debug=self.debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # sending CMD", debug=self.debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=self.debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=self.debug)
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
            self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()  # no manual port_free.set() here as respective
            # command executed notification sets it at the right time
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # START_POWER_UNREGULATED", debug=self.debug)
        return s
    
    async def START_POWER_UNREGULATED(self,
                                      power: int = None,
                                      start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                      time_to_stalled: float = 1.0,
                                      on_stalled: Awaitable = None,
                                      delay_before: float = None,
                                      delay_after: float = None,
                                      wait_cond: Callable = None,
                                      wait_cond_timeout: float = None, ):
        await self.START_POWER_UNREGULATED_SYNCED(power_a=power,
                                                  power_b=power,
                                                  start_cond=start_cond,
                                                  time_to_stalled=time_to_stalled,
                                                  on_stalled=on_stalled,
                                                  delay_before=delay_before,
                                                  delay_after=delay_after,
                                                  wait_cond=wait_cond,
                                                  wait_cond_timeout=wait_cond_timeout, )
        return
    
    async def START_POWER_UNREGULATED_SYNCED(self,
                                             power_a: int = None,
                                             power_b: int = None,
                                             start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                             time_to_stalled: float = 1.0,
                                             on_stalled: Awaitable = None,
                                             delay_before: float = None,
                                             delay_after: float = None,
                                             wait_cond: Callable = None,
                                             wait_cond_timeout: float = None,
    
                                             ):
        """
        
        Keyword Args
        ---
        power_a (int):
        power_b (int):
        use_profile ():
        use_acc_profile ():
        use_decc_profile ():
        start_cond ():

        Returns
        ---

        """
        
        power_a *= self._forward_direction_a  # normalize power motor A
        power_b *= self._forward_direction_b  # normalize power motor B
        
        debug_info_header(f"NAME: {self.name} / PORT: {self.port[0]} # START_POWER_UNREGULATED_SYNCED", debug=self.debug)
        debug_info_begin(f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # WAITING AT THE GATES",
                         debug=self.debug)
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            debug_info_end(f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # PASSED THE GATES",
                           debug=self.debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
            
            current_command = CMD_START_PWR_DEV(
                    synced=True,
                    port=self._port,
                    power_a=power_a,
                    power_b=power_b,
                    start_cond=start_cond,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                    )
            
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # sending CMD", debug=self.debug)
            # _wait_until part
            if wait_cond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(wait_cond, fut)
                done = await asyncio.wait_for(fut, timeout=wait_cond_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            # stalled condition part
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self._cmd_send(current_command)
            debug_info(f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # CMD: {current_command}",
                       debug=self.debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # sending CMD", debug=self.debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=self.debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=self.debug)
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
            self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()  # no manual port_free.set() here as respective
            # command executed notification sets it at the right time
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # START_POWER_UNREGULATED", debug=self.debug)
        return s
    
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
    
    async def hub_attached_io_notification_set(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        former_port = self._port
        debug_info_header(f"VIRTUAL PORT {self._port[0]}: HUB_ATTACHED_IO_NOTIFICATION:", debug= self._debug)
        if io_notification.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED:
            debug_info(f"PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED?: {io_notification.m_io_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED}", debug=self._debug)
            
            self._hub_attached_io = io_notification
            self._port = io_notification.m_port
            self._motor_a_port = io_notification.m_port_a
            self._motor_b_port = io_notification.m_port_b
            
            self._ext_srv_connected.set()
            self._ext_srv_disconnected.clear()
            self._port2hub_connected.set()
            self._port_connected.set()
            self._port_free.set()
        
        elif io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED:
            debug_info(f"PERIPHERAL_EVENT.IO_DETACHED?: {io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED}", debug= self._debug)
            
            self._port_connected.clear()
            self._ext_srv_connected.clear()
            self._ext_srv_disconnected.set()
            self._port2hub_connected.clear()
            self._port_free.clear()
        
        debug_info(f"FORMER PORT: {int.from_bytes(former_port, 'little', signed=False)}", debug=self._debug)
        debug_info(f"NEW VIRTUAL PORT: {int.from_bytes(self._port, 'little', signed=False)}", debug=self._debug)
        debug_info(f"PORT A: {int.from_bytes(self._motor_a.port, 'little', signed=False)}", debug=self._debug)
        debug_info(f"PORT B: {int.from_bytes(self._motor_b.port, 'little', signed=False)}", debug=self._debug)
        debug_info(f"EXT_SRV_CONNECTED?:    {self._ext_srv_connected.is_set()}{C.ENDC}", debug=self._debug)
        debug_info(f"EXT_SRV_DISCONNECTED?: {self._ext_srv_disconnected.is_set()}{C.ENDC}", debug=self._debug)
        debug_info(f"PORT2HUB_CONNECTED?:   {self._port2hub_connected.is_set()}{C.ENDC}", debug=self._debug)
        debug_info(f"PORT_FREE?:            {self._port_free.is_set()}{C.ENDC}", debug=self._debug)
        debug_info_footer(footer=f"VIRTUAL PORT {self._port[0]}: HUB_ATTACHED_IO_NOTIFICATION:", debug=self._debug)
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
        return self._acc_dec_profiles
    
    @acc_dec_profiles.setter
    def acc_dec_profiles(self, profiles: defaultdict):
        self._acc_dec_profiles = profiles
        return
    
    async def START_MOVE_DEGREES(
            self,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed: int = 0,
            abs_max_power: int = 0,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
            on_stalled: Awaitable = None,
            time_to_stalled: float = 1.0,
            delay_before: float = None,
            delay_after: float = None,
            wait_cond: Callable = None,
            wait_cond_timeout: float = None
            ):
        await self.START_MOVE_DEGREES_SYNCED(start_cond=start_cond,
                                             completion_cond=completion_cond,
                                             degrees=degrees,
                                             speed_a=speed,
                                             speed_b=speed,
                                             abs_max_power=abs_max_power,
                                             on_completion=on_completion,
                                             use_profile=use_profile,
                                             use_acc_profile=use_acc_profile,
                                             use_dec_profile=use_dec_profile,
                                             on_stalled=on_stalled,
                                             time_to_stalled=time_to_stalled,
                                             delay_before=delay_before,
                                             delay_after=delay_after,
                                             wait_cond=wait_cond,
                                             wait_cond_timeout=None, )
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
            use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
            on_stalled: Awaitable = None,
            time_to_stalled: float = 1.0,
            delay_before: float = None,
            delay_after: float = None,
            wait_cond: Callable = None,
            wait_cond_timeout: float = None
            ):
        
        speed_a *= self._forward_direction_a  # normalize speed motor A
        speed_b *= self._forward_direction_b  # normalize speed motor B
        degrees *= self._forward
        debug_info_header(f"NAME: {self.name} / PORT: {self.port[0]} # START_MOVE_DEGREES_SYNCED", debug=self.debug)
        debug_info_begin(
                f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # WAITING AT THE GATES",
                debug=self.debug)
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            self._motor_a.port_free.clear()
            self._motor_b.port_free.clear()
            debug_info_end(f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # PASSED THE GATES",
                           debug=self.debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
            
            current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    degrees=int(round(round(degrees * self.gearRatio[0]) + round(degrees * self.gearRatio[1]) / 2)),
                    # not really ok, needs better thinking
                    speed_a=speed_a,
                    speed_b=speed_b,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile, )
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # sending CMD", debug=self.debug)
            # _wait_until part
            if wait_cond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(wait_cond, fut)
                done = await asyncio.wait_for(fut, timeout=wait_cond_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            # stalled condition part
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self._cmd_send(current_command)
            debug_info(f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # CMD: {current_command}",
                       debug=self.debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # sending CMD", debug=self.debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # delay_after {delay_after}s",
                        debug=self.debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_MOVE_DEGREES_SYNCED # delay_after {delay_after}s",
                        debug=self.debug)
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
            self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()  # no manual port_free.set() here as respective
            # command executed notification sets it at the right time
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # START_MOVE_DEGREES_SYNCED", debug=self.debug)
        return s
    
    async def START_SPEED_TIME(self,
                               time: int,
                               speed: int,
                               start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                               completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                               power: int = 50,
                               on_completion: int = MOVEMENT.BREAK,
                               use_profile: int = 0,
                               use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
                               use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
                               on_stalled: Awaitable = None,
                               time_to_stalled: float = 1.0,
                               delay_before: float = None,
                               delay_after: float = None,
                               wait_cond: Callable = None,
                               wait_cond_timeout: float = None,
                               ):
        await self.START_SPEED_TIME_SYNCED(time=time,
                                           speed_a=speed,
                                           speed_b=speed,
                                           start_cond=start_cond,
                                           completion_cond=completion_cond,
                                           power=power,
                                           on_completion=on_completion,
                                           use_profile=use_profile,
                                           use_acc_profile=use_acc_profile,
                                           use_dec_profile=use_dec_profile,
                                           on_stalled=on_stalled,
                                           time_to_stalled=time_to_stalled,
                                           delay_before=delay_before,
                                           delay_after=delay_after,
                                           wait_cond=wait_cond,
                                           wait_cond_timeout=wait_cond_timeout, )
        return
    
    async def START_SPEED_TIME_SYNCED(
            self,
            time: int,
            speed_a: int,
            speed_b: int,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            power: int = 50,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
            on_stalled: Awaitable = None,
            time_to_stalled: float = 1.0,
            delay_before: float = None,
            delay_after: float = None,
            wait_cond: Callable = None,
            wait_cond_timeout: float = None,
            ):
        """

        Parameters
        ----------
        
        on_stalled : Awaitable
        wait_cond :
        start_cond :
        completion_cond :
        time :
        speed_a :
        speed_b :
        power :
        on_completion :
        use_profile :
        use_acc_profile :
        use_dec_profile :
        time_to_stalled :
        wait_cond_timeout :
        delay_before :
        delay_after :

        Returns
        -------

        """
        
        speed_a *= self._forward_direction_a  # normalize speed motor A
        speed_b *= self._forward_direction_b  # normalize speed motor B
        power *= self._forward  # normalize power motors
        
        debug_info_header(f"NAME: {self.name} / PORT: {self.port[0]} # START_SPEED_TIME_SYNCED", debug=self.debug)
        debug_info_begin(
                f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # WAITING AT THE GATES",
                debug=self.debug)
        async with self.port_free_condition, self._motor_a.port_free_condition, self._motor_b.port_free_condition:
            await self.port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            await self._motor_a.port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set())
            self._motor_a.port_free.clear()
            await self._motor_b.port_free_condition.wait_for(lambda: self._motor_b.port_free.is_set())
            self._motor_b.port_free.clear()
            self._command_end.clear()
            debug_info_end(f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # PASSED THE GATES",
                           debug=self.debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # delay_before {delay_before}s",
                        debug=self.debug)
            
            current_command = CMD_START_MOVE_DEV_TIME(
                    synced=True,
                    port=self._port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    time=time,
                    speed_a=speed_a,
                    speed_b=speed_b,
                    power=power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile, )
            
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # sending CMD", debug=self.debug)
            # _wait_until part
            if wait_cond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(wait_cond, fut)
                done = await asyncio.wait_for(fut, timeout=wait_cond_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            # stalled condition part
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self._cmd_send(current_command)
            debug_info(f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # CMD: {current_command}",
                       debug=self.debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # sending CMD", debug=self.debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # delay_after {delay_after}s",
                        debug=self.debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME_SYNCED # delay_after {delay_after}s",
                        debug=self.debug)
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
            self.E_MOTOR_STALLED.clear()
            t0 = monotonic()
            debug_info(f"WAITING FOR COMMAND END: {t0}",  debug=self._debug)
            await self._command_end.wait()
            debug_info(f"WAITED {monotonic() - t0}s FOR COMMAND TO END...", debug=self._debug)
            self._port_free.set()
            self._motor_a.port_free.set()
            self._motor_b.port_free.set()
            self._motor_a.port_free_condition.notify_all()
            self._motor_b.port_free_condition.notify_all()
            self._port_free_condition.notify_all()  # no manual port_free.set() here as respective
            # command executed notification sets it at the right time
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # START_SPEED_TIME_SYNCED", debug=self.debug)
        return s
    
    async def GOTO_ABS_POS(self,
                           abs_pos: int,
                           start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                           completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                           speed: int = 30,
                           abs_max_power: int = 50,
                           on_completion: int = MOVEMENT.BREAK,
                           use_profile: int = 0,
                           use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
                           use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
                           time_to_stalled: float = 1.0,
                           on_stalled: Awaitable = None,
                           delay_before: float = None,
                           delay_after: float = None,
                           wait_cond: Callable = None,
                           wait_cond_timeout: float = None,
                           ):
        await self.GOTO_ABS_POS_SYNCED(abs_pos_a=abs_pos,
                                       abs_pos_b=abs_pos,
                                       start_cond=start_cond,
                                       completion_cond=completion_cond,
                                       speed=speed,
                                       abs_max_power=abs_max_power,
                                       on_completion=on_completion,
                                       use_profile=use_profile,
                                       use_acc_profile=use_acc_profile,
                                       use_dec_profile=use_dec_profile,
                                       time_to_stalled=time_to_stalled,
                                       on_stalled=on_stalled,
                                       delay_before=delay_before,
                                       delay_after=delay_after,
                                       wait_cond=wait_cond,
                                       wait_cond_timeout=wait_cond_timeout, )
        return
    
    async def GOTO_ABS_POS_SYNCED(
            self,
            abs_pos_a: int,
            abs_pos_b: int,
            start_cond: int = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: int = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed: int = 30,
            abs_max_power: int = 50,
            on_completion: int = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: int = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: int = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = 1.0,
            on_stalled: Awaitable = None,
            delay_before: float = None,
            delay_after: float = None,
            wait_cond: Callable = None,
            wait_cond_timeout: float = None,
            ):
        """Tries to reach the absolute Position as fast as possible.

        Parameters
        ----------
        
        on_stalled : Optional[Awaitable]
            Perform action if Motors are stalled.
        wait_cond : Optional[Callable]
            Wait until callable is true to proceed.
        abs_pos_a :
        abs_pos_b :
        start_cond :
        completion_cond :
        speed :
        abs_max_power :
        on_completion :
        use_profile :
        use_acc_profile :
        use_dec_profile :
        time_to_stalled :
        wait_cond_timeout :
        delay_before :
        delay_after :

        Returns
        -------

        """
        abs_pos_a *= self._clockwise_direction_a  # normalize lef/right motor A
        abs_pos_b *= self._clockwise_direction_b  # normalize lef/right motor B
        
        debug_info_header(f"{self._name}.GOTO_ABS_POS_SYNC", debug=self._debug)
        debug_info_begin(f"{self._name}.GOTO_ABS_POS_SYNC: WAITING AT THE GATES", debug=self._debug)
        async with self._port_free_condition, self._motor_a.port_free_condition, self._motor_b.port_free_condition:
            debug_info_end(f"{self._name}.GOTO_ABS_POS_SYNC: WAITING AT THE GATES", debug=self._debug)
            debug_info_begin(f"{self._name}.GOTO_ABS_POS_SYNC: AWAITING _ext_srv_connected", debug=self._debug)
            
            await self._ext_srv_connected.wait()
            debug_info_end(f"{self._name}.GOTO_ABS_POS_SYNC: AWAITING _ext_srv_connected", debug=self._debug)
            debug_info_begin(f"{self._name}.GOTO_ABS_POS_SYNC: AWAITING _port_free", debug=self._debug)
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            await self._motor_a.port_free_condition.wait_for(lambda: self._motor_a.port_free.is_set())
            self._motor_a.port_free.clear()
            await self._motor_b.port_free_condition.wait_for(lambda: self._motor_b.port_free.is_set())
            self._motor_b.port_free.clear()
            debug_info_end(f"{self._name}.GOTO_ABS_POS_SYNC: AWAITING _port_free", debug=self._debug)
            
            if delay_before is not None:
                debug_info_begin(f"{self._name}.GOTO_ABS_POS_SYNC: DELAY_BEFORE", debug=self._debug)
                debug_info(f"{C.WARNING}WAITING FOR {delay_before}", debug=self._debug)
                
                await sleep(delay_before)
                
                debug_info_end(f"{self._name}.GOTO_ABS_POS_SYNC: DELAY_BEFORE", debug=self._debug)
            
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
                    use_dec_profile=use_dec_profile,
                    )
            
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / CMD_GOTO_ABS_POS_DEV # sending CMD", debug=self.debug)
            # _wait_until part
            if wait_cond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(wait_cond, fut)
                done = await asyncio.wait_for(fut, timeout=wait_cond_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            # stalled condition part
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self._cmd_send(current_command)
            debug_info(f"NAME: {self.name} / PORT: {self.port[0]} / CMD_GOTO_ABS_POS_DEV # CMD: {current_command}",
                       debug=self.debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port[0]} / CMD_GOTO_ABS_POS_DEV # sending CMD", debug=self.debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / CMD_GOTO_ABS_POS_DEV # delay_after {delay_after}s",
                        debug=self.debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / CMD_GOTO_ABS_POS_DEV # delay_after {delay_after}s",
                        debug=self.debug)
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
            self.E_MOTOR_STALLED.clear()
            await self._command_end.wait()
            self.port_free_condition.notify_all()  # no manual port_free.set() here as respective
            # command executed notification sets it at the right time
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # CMD_GOTO_ABS_POS_DEV", debug=self.debug)
        return s
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        return self._current_cmd_feedback_notification
    
    async def cmd_feedback_notification_set(self, notification: PORT_CMD_FEEDBACK):
        debug_info_header(f"PORT {notification.m_port[0]}: PORT_CMD_FEEDBACK", debug=self._debug)
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x01', 'little'):
            debug_info(f"{notification.m_port[0]}: RECEIVED CMD_STATUS: CMD STARTED ", debug=self._debug)
            debug_info(f"STATUS: {notification.COMMAND[len(notification.COMMAND) - 1]}", debug=self._debug)
            self._command_end.clear()
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x0a', 'little'):
            debug_info(f"PORT {notification.m_port[0]}: RECEIVED CMD_STATUS: CMD FINISHED ", debug=self._debug)
            debug_info(f"STATUS: {notification.COMMAND[len(notification.COMMAND) - 1]}", debug=self._debug)
            self._command_end.set()
        
        debug_info_footer(footer=f"PORT {notification.m_port[0]}: PORT_CMD_FEEDBACK", debug=self._debug)
        
        self._cmd_feedback_log.append((datetime.timestamp(datetime.now()), notification.m_cmd_status))
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
        debug_info(f"[{self._name}:{self._port[0]}]-[MSG]: RECEIVED CONNECTION", debug=self._debug)
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
