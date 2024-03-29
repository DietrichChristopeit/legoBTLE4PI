﻿"""
legoBTLE.device.SingleMotor
===========================

A concrete :class:`AMotor`.
    
"""
import uuid
from asyncio import Condition, Task
from asyncio import Event
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter
from collections import defaultdict
from datetime import datetime
from typing import Awaitable, Callable, List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np

from legoBTLE.device.AMotor import AMotor
from legoBTLE.legoWP.message.downstream import DOWNSTREAM_MESSAGE
from legoBTLE.legoWP.message.upstream import DEV_GENERIC_ERROR_NOTIFICATION
from legoBTLE.legoWP.message.upstream import DEV_PORT_NOTIFICATION
from legoBTLE.legoWP.message.upstream import EXT_SERVER_NOTIFICATION
from legoBTLE.legoWP.message.upstream import HUB_ACTION_NOTIFICATION
from legoBTLE.legoWP.message.upstream import HUB_ALERT_NOTIFICATION
from legoBTLE.legoWP.message.upstream import HUB_ATTACHED_IO_NOTIFICATION
from legoBTLE.legoWP.message.upstream import PORT_CMD_FEEDBACK
from legoBTLE.legoWP.message.upstream import PORT_VALUE
from legoBTLE.legoWP.types import CMD_FEEDBACK_MSG
from legoBTLE.legoWP.types import MOVEMENT
from legoBTLE.legoWP.types import PERIPHERAL_EVENT
from legoBTLE.legoWP.types import PORT
from legoBTLE.networking.prettyprint.debug import debug_info
from legoBTLE.networking.prettyprint.debug import debug_info_begin
from legoBTLE.networking.prettyprint.debug import debug_info_end
from legoBTLE.networking.prettyprint.debug import debug_info_footer
from legoBTLE.networking.prettyprint.debug import debug_info_header


class SingleMotor(AMotor):
    """A single motor.
    
    Objects from this class represent a single LEGO\ |copy| Motor.
    
    """

    def __init__(self,
                 server: Tuple[str, int],
                 port: Union[PORT, int, bytes],
                 name: str = 'SingleMotor',
                 on_stall: Callable[[], Awaitable] = None,
                 time_to_stalled: float = 0.05,
                 stall_bias: float = 0.2,
                 wheel_diameter: float = 100.0,
                 gear_ratio: float = 1.0,
                 clockwise: MOVEMENT = MOVEMENT.CLOCKWISE,
                 max_steering_angle: float = None,
                 debug: bool = False,
                 ):
        """This object models a single motor at a certain port.
        
        Parameters
        ----------
        server : Tuple[str, int]
            Tuple with (Host, Port) Information, e.g., ('127.0.0.1', 8888).
        port : Union[PORT, int, bytes]
            The port, e.g., b'\x02' of the SingleMotor (:class:`legoBTLE.legoWP.types.PORT` can be utilised).
        name : str, default 'SingleMotor'
            A friendly name of this Motor device, e.g., 'FORWARD_MOTOR'.
        on_stall: Callable[[], Awaitable], optional
            The action when stalling is signalled.
        time_to_stalled : float, default 0.05
            The time of no motor movement during a move command after which the motor is deemed stalled.
        clockwise : MOVEMENT, default MOVEMENT.CLOCKWISE
            Defines what a clockwise turning means in reality and v.v.. Used to adapt the model to reality.
        gear_ratio : float, default 1.0
            The ratio of the number of teeth of the turning gear to the number of teeth of the turned gear.
        
        Other Parameters
        ----------------
        stall_bias : float, default 0.2
            The range :math:`[-$stall_bias$, $stall_bias$]` of degrees between which a moving motor is still considered stalled.
        wheel_diameter : float, default 100.0
            The diameter in mm of the attached wheel. Used for determining the traveled distance in mm.
        max_steering_angle : float, optional
            Defines the absolute maximum angle the motor can safely turn in each direction from position 0.0 before
            stalling. Usually the user calculates this value by issuing a set of commands.
        debug : bool
            ``True`` turns debugging on, ``False`` otherwise.
        
        Examples
        --------
            TO_DO
            
        """
        
        self._id: str = uuid.uuid4().hex
        self._synced: bool = False
        
        self._name: str = name  # just to get a nice printout
        self._DEVNAME = ''.join(name.split(' '))
        
        if isinstance(port, PORT):
            self._port: bytes = port.value
        elif isinstance(port, int):
            self._port: bytes = int.to_bytes(port, length=1, byteorder='little', signed=False)
        else:
            self._port: bytes = port.to_bytes()
        
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()

        self._E_CMD_STARTED: Event = Event()
        self._E_CMD_FINISHED: Event = Event()
        self._set_cmd_running(False)
        self.__e_port_value_rcv: Event = Event()  # has some value already been received
        
        self._time_to_stalled: float = time_to_stalled
        self._stall_bias: float = stall_bias
        self._ON_STALLED_ACTION: Optional[Callable[[], Awaitable]] = on_stall
        self._E_MOTOR_STALLED: Event = Event()
        self._E_DETECT_STALLING: Event = Event()
        self._stall_guard: Optional[Task] = None
    
        self._last_cmd_snt: Optional[DOWNSTREAM_MESSAGE] = None
        self._last_cmd_failed: Optional[DOWNSTREAM_MESSAGE] = None
        
        self._current_cmd_feedback_notification: Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: Optional[str] = None
        self._cmd_feedback_log: List[Tuple[float, CMD_FEEDBACK_MSG]] = []
        
        self._server: [str, int] = server
        self._ext_srv_connected: Event = Event()
        self._port2hub_connected: Event = Event()
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: Optional[List[Tuple[float, EXT_SERVER_NOTIFICATION]]] = None
        self._connection: Optional[Tuple[StreamReader, StreamWriter]] = None
        self._error: Event = Event()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_disconnected.set()
        self._hub_alert: Event = Event()
        
        self._port_notification: Optional[DEV_PORT_NOTIFICATION] = None
    
        self._wheel_diameter: float = wheel_diameter
        self._gear_ratio: float = gear_ratio
        self._distance: float = 0.0
        self._total_distance: float = 0.0
        
        self._current_value: Optional[PORT_VALUE] = None
        self._last_value: Optional[PORT_VALUE] = None
        
        self._measure_distance_start = None
        self._measure_distance_end = None
        self._abs_max_distance = None
        
        self._avg_speed: float = 0.0
        self._max_avg_speed: float = 0.0
        
        self._error_notification: Optional[DEV_GENERIC_ERROR_NOTIFICATION] = None
        self._error_notification_log: List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]] = []
        
        self._hub_action_notification: Optional[HUB_ACTION_NOTIFICATION] = None
        self._hub_attached_io_notification: Optional[HUB_ATTACHED_IO_NOTIFICATION] = None
        self._hub_alert_notification: Optional[HUB_ALERT_NOTIFICATION] = None
        self._hub_alert_notification_log: List[Tuple[float, HUB_ALERT_NOTIFICATION]] = []
        
        self._acc_dec_profiles: defaultdict = defaultdict(defaultdict)
        self._current_profile: defaultdict = defaultdict(None)
        
        self._clockwise_direction: MOVEMENT = clockwise
        
        self._max_steering_angle: float = max_steering_angle
        
        self._debug: bool = debug

        # super(AMotor).__init__(SingleMotor)
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
    def synced(self) -> bool:
        return self._synced
    
    @property
    def port2hub_connected(self) -> Event:
        return self._port2hub_connected

    @property
    def clockwise_direction(self) -> MOVEMENT:
        return self._clockwise_direction

    @clockwise_direction.setter
    def clockwise_direction(self, real_clockwise_direction: MOVEMENT):
        self._clockwise_direction = real_clockwise_direction
        return
    
    @property
    def max_steering_angle(self) -> float:
        return self._max_steering_angle
    
    @max_steering_angle.setter
    def max_steering_angle(self, max_steering_angle: float):
        self._max_steering_angle = max_steering_angle
        return
    
    @property
    def total_distance(self) -> float:
        """The total travelled distance in mm.
        
        The property respects gear ratio and wheel wheel_diameter. It acts like the eternal odometer of a car.
        
        Returns
        -------
        out : float
            The total distance travelled in mm.

        Notes
        -----
        The underlying formula is:

        .. math::
            ``dist_{mm} = \frac{total_distance * gear_ratio * \Pi * wheel_diameter}{360}``

            :math:``\frac{\sum_{i=1}^{\infty} x_{i}}{\infty}``
        """
        return self._total_distance * self._gear_ratio * np.pi * self._wheel_diameter / 360
    
    @total_distance.setter
    def total_distance(self, distance: float):
        self._total_distance = distance
        return
    
    @property
    def distance(self) -> float:
        return self._distance
    
    @distance.setter
    def distance(self, distance: float):
        self._distance = distance
        return

    @property
    def avg_speed(self) -> float:
        return self._avg_speed

    @avg_speed.setter
    def avg_speed(self, avg_speed: float):
        self._avg_speed = avg_speed
        if self._avg_speed > self._max_avg_speed:
            self._max_avg_speed = self._avg_speed
        return

    @property
    def max_avg_speed(self) -> float:
        return self._max_avg_speed

    @property
    def port_value(self) -> PORT_VALUE:
        return self._current_value
    
    async def port_value_set(self, value: PORT_VALUE) -> None:
        """Set the Port value.
        
        Parameters
        ----------
        value : :class:`PORT_VALUE`
            The value notification to set for this port

        Returns
        -------
        None
        """
        self._last_value = self._current_value if self._current_value is not None else value
        self._current_value = value
        self.__e_port_value_rcv.set()
        debug_info(f"{self._name}:{self._port[0]} >>>>>>>> CURRENTVALUE: {value.m_port_value_DEG}", debug=self.debug)
        self._total_distance += abs(self._current_value.m_port_value_DEG - self._last_value.m_port_value_DEG)
        
        return
    
    @property
    def _e_port_value_rcv(self) -> Event:
        return self.__e_port_value_rcv
    
    @property
    def last_value(self) -> PORT_VALUE:
        return self._last_value

    @property
    def time_to_stalled(self) -> float:
        return self._time_to_stalled

    @time_to_stalled.setter
    def time_to_stalled(self, tts: float):
        self._time_to_stalled = tts
        return

    @property
    def E_MOTOR_STALLED(self) -> Event:
        return self._E_MOTOR_STALLED
    
    @property
    def ON_STALLED_ACTION(self) -> Callable[[], Awaitable]:
        return self._ON_STALLED_ACTION
    
    @ON_STALLED_ACTION.setter
    def ON_STALLED_ACTION(self, action: Callable[[], Awaitable]):
        self._ON_STALLED_ACTION = action
        return
    
    @ON_STALLED_ACTION.deleter
    def ON_STALLED_ACTION(self):
        del self._ON_STALLED_ACTION
        return
    
    @property
    def stall_guard(self) -> Task:
        return self._stall_guard
    
    @stall_guard.setter
    def stall_guard(self, stall_guard: Task) -> None:
        self._stall_guard = stall_guard
        return
    
    @property
    def stall_bias(self) -> float:
        """The tolerance under which the motor is deemed stalled.

        Returns
        -------
        float
            The tolerance.
            
        """
        return self._stall_bias

    @stall_bias.setter
    def stall_bias(self, stall_bias: float):
        self._stall_bias = stall_bias
    
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
    
    @property
    def port_free_condition(self) -> Condition:
        return self._port_free_condition
    
    @property
    def port_free(self) -> Event:
        return self._port_free

    @property
    def E_CMD_STARTED(self) -> Event:
        return self._E_CMD_STARTED

    @property
    def E_CMD_FINISHED(self) -> Event:
        return self._E_CMD_FINISHED
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        return self._port_notification
    
    async def port_notification_set(self, notification: DEV_PORT_NOTIFICATION) -> None:
        print(f"IN PORT NOTIFICATION: {self._name}")
        if notification.m_status == PERIPHERAL_EVENT.IO_ATTACHED:
            self._port_free.set()
            self._port2hub_connected.set()
        elif notification.m_status == PERIPHERAL_EVENT.IO_DETACHED:
            self._port_free.clear()
            self._port2hub_connected.clear()
        self._port_notification = notification
        return
    
    @property
    def server(self) -> (str, int):
        return self._server
    
    @server.setter
    def server(self, server: Tuple[int, str]) -> None:
        """Sets new Server information.
        
        :param tuple[int, str] server: The host and port of the server.
        :return: None
        
        """
        self._server = server
    
    @property
    def connection(self) -> Tuple[StreamReader, StreamWriter]:
        return self._connection
    
    def connection_set(self, connection: Tuple[StreamReader, StreamWriter]) -> None:
        """Sets a new Server <-> device Read/write connection.
        
        Parameters
        ----------
        connection : tuple[StreamReader, StreamWriter]
            The connection.
        
        Returns
        -------
        None
            Nothing, setter.
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
        """Return the Hub's error notification.

        :return: The generic error sent by the hub.
        :rtype: :class:`DEV_GENERIC_ERROR_NOTIFICATION`
        """
        return self._error_notification
    
    async def error_notification_set(self, error: DEV_GENERIC_ERROR_NOTIFICATION) -> None:
        """Sets an incoming error notification sent from the hub.

        Only if receiving error notifications has been requested before.

        :param error: The Hub's error notification
        :type error: :class:`DEV_GENERIC_ERROR_NOTIFICATION`
        :return: Setter, nothing.
        :rtype: None
        
        .. seealso:: `LEGO(c) Generic Error Messages <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#generic-error-messages>`_
        
        """
        self._error_notification = error
        self._error.set()
        self._error_notification_log.append((datetime.timestamp(datetime.now()), error))
        return
    
    @property
    def error_notification_log(self) -> List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]]:
        return self._error_notification_log
    
    @property
    def wheel_diameter(self) -> float:
        return self._wheel_diameter
    
    @wheel_diameter.setter
    def wheel_diameter(self, wheel_diameter: float = 100.0):
        """Set the wheel diameter.
        
        Parameters
        ----------
        wheel_diameter: float, default 100
            The wheel diameter in mm.

        Returns
        -------
        None
            Nothing
        """
        self._wheel_diameter = wheel_diameter
        return

    @property
    def gear_ratio(self) -> float:
        """Get the gear ratio of this :class:`SingleMotor`.
        """
        return self._gear_ratio
    
    @gear_ratio.setter
    def gear_ratio(self, gear_ratio: float = 1.0) -> None:
        """Set the gear_ratio of a :class:`legoBTLE.device.SingleMotor`.

        Parameters
        ----------
        gear_ratio : float, default 1
            The ratio of gear teeth of the driving gear to the driven gear.
        
        Returns
        -------
        None
            Setter, nothing
        """
        
        self._gear_ratio = gear_ratio
        return
    
    @property
    def ext_srv_connected(self) -> Event:
        """Returns an Event indicating the status of an external server connection.
        
        Returns
        -------
        ext_srv_connected : Event
            The :class:``Event`` is set is the external server is connected, un-set otherwise.
        
        """
        return self._ext_srv_connected
    
    @property
    def ext_srv_disconnected(self) -> Event:
        return self._ext_srv_disconnected
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        """
        
        The last received Notification from the external server.
        
        Returns
        -------
        EXT_SERVER_NOTIFICATION
            The last Notification received from the server.
            
        """
        return self._ext_srv_notification
    
    async def ext_srv_notification_set(self, notification: EXT_SERVER_NOTIFICATION, debug: bool = False):
        """Set an :class:`EXT_SRV_NOTIFICATION`.
        
        This method is used to receive notifications from the external server. The messages are stored in a log if
        `debug` is ``True``.
        
        This function is a Coroutine, so that message reception does not block the EventLoop.
        
        Parameters
        ----------
        notification : EXT_SERVER_NOTIFICATION
            The notification sent by the server.
        debug : bool
            If ``True`` produce verbose output and store this notification in a log.

        """
        debug = self._debug if debug is None else debug
        
        debug_info_header(f"[{self._name}].[{__name__}]", debug)
        if notification is not None:
            self._ext_srv_notification = notification
            print(f"IN EXTSERVER_NOTIFICATION: {self._name} / NOT NONE {bytes(self._ext_srv_notification.m_event)} / TYPE: {PERIPHERAL_EVENT.EXT_SRV_CONNECTED}")
            print(f"COMPARISON: {bytes(self._ext_srv_notification.m_event) == PERIPHERAL_EVENT.EXT_SRV_CONNECTED}")
            # if self._debug:
              #  self._ext_srv_notification_log.append((datetime.timestamp(datetime.now()), notification))
            if self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_CONNECTED:
                self._ext_srv_connected.set()
                self._ext_srv_disconnected.clear()
                self._port2hub_connected.set()
                self._port_free.set()
                print(f"IN EXTSERVER_NOTIFICATION: {self._name} / NOTIFICATION: SUCCESS")
            elif self._ext_srv_notification.m_event == PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED:
                self._connection[1].close()
                self._ext_srv_connected.clear()
                self._ext_srv_disconnected.set()
                self._port2hub_connected.clear()
                self._port_free.clear()
                print(f"IN EXTSERVER_NOTIFICATION: {self._name} / NOTIFICATION: DISCONNECTED SUCCESS")
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
        """The latest HUB-ATTACHED-IO-Message.
        
        A detailed description of the format of the message and its attributes' meanings can be found in
        `HUB ATTACHED IO: LEGO(c) Wireless Protocol 3.0.00r17 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#hub-attached-i-o>`_
        
        Returns
        -------
        HUB_ATTACHED_IO_NOTIFICATION
            The latest HUB-ATTACHED-IO-Message received.
        """
        return self._hub_attached_io_notification
    
    async def hub_attached_io_notification_set(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION):
        """
        A detailed description of the format of the message and its attributes' meanings can be found in
        `HUB ATTACHED IO: LEGO(c) Wireless Protocol 3.0.00r17 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#hub-attached-i-o>`_
        
        Parameters
        ----------
        io_notification : HUB_ATTACHED_IO_NOTIFICATION
            The notification regarding the connection status of this motor.

        Returns
        -------
        None
            This is a setter.
        """
        self._hub_attached_io_notification = io_notification
        if io_notification.m_io_event == PERIPHERAL_EVENT.IO_ATTACHED:
            debug_info(
                    f"[{self._name}:{self._port[0]}]-[MSG]: MOTOR {self._name} is ATTACHED... "
                    f"{io_notification.m_device_type}", debug=self._debug)
            self.ext_srv_connected.set()
            self._ext_srv_disconnected.clear()
            self._port_free.set()
            self._port2hub_connected.set()
        elif io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED:
            debug_info(f"[{self._name}:{self._port[0]}]-[MSG]: MOTOR {self._name} is DETACHED...", debug=self._debug)
            self.ext_srv_connected.clear()
            self._ext_srv_disconnected.set()
            self._port_free.clear()
            self._port2hub_connected.clear()
        
        return
    
    @property
    def measure_start(self) -> Tuple[float, float]:
        self._measure_distance_start = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        debug_info(f"[{self._name}:{self._port[0]}]-[TIME_STOP]: STOP TIME: {self._measure_distance_end[1]}\t"
                  f"VALUE: {self._measure_distance_end[0]}", debug=self._debug)
        return self._measure_distance_start
    
    @property
    def measure_end(self) -> Tuple[float, float]:
        self._measure_distance_end = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        debug_info(f"[{self._name}:{self._port[0]}]-[TIME_STOP]: STOP TIME: {self._measure_distance_end[1]}\t"
                  f"VALUE: {self._measure_distance_end[0]}", debug=self._debug)
        return self._measure_distance_end
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        """Latest received feedback regarding this port.
        
        A detailed description of the port command feedback format can be found in
        `LEGO(c) Wireless Protocol 3.0.00r.17 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-output-command-feedback-format>`_
        
        Returns
        -------
        PORT_CMD_FEEDBACK
            The latest feedback concerning th configuration of this motor's port.
            
        """
        return self._current_cmd_feedback_notification
    
    async def cmd_feedback_notification_set(self, notification: PORT_CMD_FEEDBACK):
        r"""Receiving and processing command feedbacks.
        
        The feedbacks from commands are processed here. This method is a preliminary implementation of the SDK state
        machine as outlined in `COMMAND FEEDBACK: LEGO(c) Wireless Protocol 3.0.00 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-output-command-feedback-format>`_

        Parameters
        ----------
        notification : PORT_CMD_FEEDBACK
            The latest command feedback as received from the hub brick.

        Returns
        -------
        None
            This is a setter
            
        """
        debug_info_header(f"<{self.name} -- {self.port[0]}> - CMD_FEEDBACK", debug=self._debug)
        debug_info_begin(f"<{self.name}:{self.port[0]}> - CMD_FEEDBACK: NOTIFICATION-MSG-DETAILS", debug=self._debug)
        debug_info(f"<{self.name}:{self.port[0]}> - <CMD_FEEDBACK]: PORT: {notification.m_port[0]}", debug=self._debug)
        debug_info(f"<{self.name}:{self.port[0]}> - <CMD_FEEDBACK]: MSG_CONTENT: {notification.COMMAND.hex()}", debug=self._debug)
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x01', 'little'):
            
            debug_info(f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]: CMD-STATUS: CMD STARTED", debug=self._debug)
            debug_info(f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]: CMD-STATUS CODE: {notification.COMMAND[len(notification.COMMAND) - 1]}", debug=self._debug)
            
            self._set_cmd_running(True)
            if self._stall_guard is None:  # if stall_guard not running start it
                self.__e_port_value_rcv.clear()
                await self._stall_detection_init(f"{self._name}.STALL_GUARD INITIALISED", debug=self._debug)  # stall_guard now running
                debug_info(f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]:\tSTALL_GUARD RUNNING", debug=self._debug)
            self._E_DETECT_STALLING.set()
            
            self._port_free.clear()
            
            debug_info_end(f"[{self.name}:{self.port[0]}]-[CMD_FEEDBACK]: NOTIFICATION-MSG-DETAILS:{notification.m_port[0]}",
                           debug=self._debug)
            
        elif notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x0a', 'little'):
            debug_info(f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]: REPORTED CMD-STATUS: CMD EXECUTED",
                       debug=self._debug)
            debug_info(
                    f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]: CMD-STATUS CODE: {notification.COMMAND[len(notification.COMMAND) - 1]}",
                    debug=self._debug)
            
            self._set_cmd_running(False)
            self.__e_port_value_rcv.clear()
            self._port_free.set()
            
            # self.E_MOTOR_STALLED.clear()
            
            debug_info_end(
                    f"[{self.name}:{self.port[0]}]-[CMD_FEEDBACK]: NOTIFICATION-MSG-DETAILS:{notification.m_port[0]}",
                    debug=self._debug)
        else:
            debug_info(f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]:REPORTED CMD-STATUS: CMD DISCARDED",
                       debug=self._debug)
            debug_info(
                f"[{self.name}:{notification.m_port[0]}]-[CMD_FEEDBACK]:CMD-STATUS CODE: {notification.COMMAND[len(notification.COMMAND) - 1]}",
                debug=self._debug)

            self._set_cmd_running(False)
            self.__e_port_value_rcv.clear()
            self.port_free.set()
            
        debug_info_end(f"[{self.name}:{self.port[0]}]-[CMD_FEEDBACK]: NOTIFICATION-MSG-DETAILS", debug=self._debug)
        debug_info_footer(f"<{self.name} -- {self.port[0]}> - CMD_FEEDBACK", debug=self._debug)
        # self._cmd_feedback_log.append((datetime.timestamp(datetime.now()), notification.m_cmd_status))
        self._current_cmd_feedback_notification = notification
        return True
    
    # b'\x05\x00\x82\x10\x0a'

    def cmd_feedback_log(self) -> List[Tuple[float, CMD_FEEDBACK_MSG]]:
        return self._cmd_feedback_log
    
    @property
    def debug(self) -> bool:
        return self._debug
