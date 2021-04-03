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
import uuid
from asyncio import Condition, Event
from asyncio.streams import StreamReader, StreamWriter
from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Tuple, Union

import numpy as np

from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import (
    DOWNSTREAM_MESSAGE,
    )

from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, EXT_SERVER_NOTIFICATION, HUB_ACTION_NOTIFICATION,
    HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK, PORT_VALUE,
    )
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG, PERIPHERAL_EVENT, PORT, C


class SingleMotor(AMotor):
    """Objects from this class represent a single Lego Motor.
    
    """
    
    def __init__(self,
                 server: [str, int],
                 port: Union[PORT, int, bytes],
                 name: str = 'SingleMotor',
                 time_to_stalled: float = 1.0,
                 wheel_diameter: float = 100.0,
                 gearRatio: float = 1.0,
                 debug: bool = False
                 ):
        """This object models a single motor at a certain port.
        
        Args:
            server (tuple[str,int]): Tuple with (Host, Port) Information, e.g., ('127.0.0.1', 8888).
            port (Union[PORT, bytes]): The port, e.g., b'\x02' of the SingleMotor (LegoBTLE.Constants.Port can be
            utilised).
            name (str): A friendly name of the this Motor Device, e.g., 'FORWARD_MOTOR'.
            gearRatio (float): The ratio of the number of teeth of the turning gear to the number of teeth of the
            turned gear.
            debug (bool): Turn on/off debug Output.
            
        """
        self._id: str = uuid.uuid4().hex
        
        self._DEVNAME = ''.join(name.split(' '))
        
        self._error: Event = Event()
        self._ext_srv_disconnected: Event = Event()
        self._ext_srv_disconnected.set()
        self._hub_alert: Event = Event()
        self._name: str = name
        
        if isinstance(port, PORT):
            self._port: bytes = port.value
        elif isinstance(port, int):
            self._port: bytes = int.to_bytes(port, length=1, byteorder='little', signed=False)
        else:
            self._port: bytes = port
        
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()
        self.time_to_stalled: float = time_to_stalled
        self._stalled: Event = Event()
        
        self._last_cmd_snt: Optional[DOWNSTREAM_MESSAGE] = None
        self._last_cmd_failed: Optional[DOWNSTREAM_MESSAGE] = None
        
        self._current_cmd_feedback_notification: Optional[PORT_CMD_FEEDBACK] = None
        self._current_cmd_feedback_notification_str: Optional[str] = None
        self._cmd_feedback_log: List[Tuple[float, CMD_FEEDBACK_MSG]] = []
        
        self._server: [str, int] = server
        self._ext_srv_connected: Event = Event()
        self._ext_srv_notification: Optional[EXT_SERVER_NOTIFICATION] = None
        self._ext_srv_notification_log: List[Tuple[float, EXT_SERVER_NOTIFICATION]] = []
        self._connection: Tuple[StreamReader, StreamWriter] = Tuple[()]
        
        self._port_notification: Optional[DEV_PORT_NOTIFICATION] = None
        self._port2hub_connected: Event = Event()
        
        self._wheelDiameter: float = wheel_diameter
        self._gearRatio: float = gearRatio
        self._distance: float = 0.0
        self._total_distance: float = 0.0
        
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
        
        self._acc_dec_profiles: defaultdict = defaultdict(defaultdict)
        self._current_profile: defaultdict = defaultdict(None)
        
        self._E_MOTOR_STALLED: Event = Event()
        self._debug: bool = debug
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
    def port2hub_connected(self) -> Event:
        return self._port2hub_connected
    
    @property
    def total_distance(self) -> float:
        """The total travelled distance in mm.
        The property respects gear ratio and wheel diameter. It acts like the eternal odometer of a car.
        
        Returns
        -------
        out : float
            The total distance travelled in mm.
            
        Notes
        -----
        The underlying formula is:
        .. math:: dist_{mm} = total_distance * gearRatio * \pi * wheelDiameter / 360
        """
        return self._total_distance * self.gearRatio * np.pi * self.wheelDiameter / 360
    
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
    def port_value(self) -> PORT_VALUE:
        return self._current_value
    
    async def port_value_set(self, value: PORT_VALUE) -> None:
        """
        
        :param PORT_VALUE value: The device val to set.
        :return: Setter, nothing.
        :rtype: None
        """
        self._last_value = self._current_value if self._current_value is not None else value
        self._current_value = value
        
        self._total_distance += abs(self._current_value.m_port_value_DEG - self._last_value.m_port_value_DEG)
        
        return
    
    @property
    def last_value(self) -> PORT_VALUE:
        return self._last_value
    
    @property
    def E_MOTOR_STALLED(self) -> Event:
        return self._E_MOTOR_STALLED
    
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
        """Return the Hub's error notification.

        :return: The generic error sent by the hub.
        :rtype: DEV_GENERIC_ERROR_NOTIFICATION
        """
        return self._error_notification
    
    async def error_notification_set(self, error: DEV_GENERIC_ERROR_NOTIFICATION) -> None:
        """Sets an incoming error notification sent from the hub.

        Only if receiving error notifications has been requested before.

        See: https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#generic-error-messages

        :param error: The Hub's error notification
        :type error: DEV_GENERIC_ERROR_NOTIFICATION
        :return: Setter, nothing.
        :rtype: None
        """
        self._error_notification = error
        self._error.set()
        self._error_notification_log.append((datetime.timestamp(datetime.now()), error))
        return
    
    @property
    def error_notification_log(self) -> List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]]:
        return self._error_notification_log
    
    @property
    def wheelDiameter(self) -> float:
        return self._wheelDiameter
    
    @wheelDiameter.setter
    def wheelDiameter(self, diameter: float = 100.0):
        """

        Keyword Args:
            diameter (float): The wheel diameter in mm.

        Returns:
            nothing (None):
        """
        
        self._wheelDiameter = diameter
        return

    @property
    def gearRatio(self) -> float:
        return self._gearRatio
    
    @gearRatio.setter
    def gearRatio(self, gearRatio: float = 1.0) -> None:
        """Set the gearRatio of a SingleMotor.

        :param gearRatio: The ratio of gear teeth of the driving gear to the driven gear.
        :type gearRatio: float


        :return: Setter, nothing
        :rtype: None
        """
        
        self._gearRatio = gearRatio
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
                print(f"[{self._name}:{self._port[0]}]-[MSG]: received CONNECTION ACK")
                self._ext_srv_connected.set()
                self._ext_srv_disconnected.clear()
                self.port2hub_connected.set()
                self.port_free.set()
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
            if self._debug:
                print(
                    f"[{self._name}:{self._port[0]}]-[MSG]: MOTOR {self._name} is ATTACHED... "
                    f"{io_notification.m_device_type}")
            self.ext_srv_connected.set()
            self._ext_srv_disconnected.clear()
            self._port_free.set()
            self._port2hub_connected.set()
        elif io_notification.m_io_event == PERIPHERAL_EVENT.IO_DETACHED:
            if self._debug:
                print(f"[{self._name}:{self._port[0]}]-[MSG]: MOTOR {self._name} is DETACHED...")
            self.ext_srv_connected.clear()
            self._ext_srv_disconnected.set()
            self._port_free.clear()
            self._port2hub_connected.clear()
        
        return
    
    @property
    def measure_start(self) -> Tuple[float, float]:
        self._measure_distance_start = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        if self._debug:
            print(f"[{self._name}:{self._port[0]}]-[TIME_STOP]: STOP TIME: {self._measure_distance_end[1]}\t"
                  f"VALUE: {self._measure_distance_end[0]}")
        return self._measure_distance_start
    
    @property
    def measure_end(self) -> Tuple[float, float]:
        self._measure_distance_end = (self._current_value.m_port_value, datetime.timestamp(datetime.now()))
        if self._debug:
            print(f"[{self._name}:{self._port[0]}]-[TIME_STOP]: STOP TIME: {self._measure_distance_end[1]}\t"
                  f"VALUE: {self._measure_distance_end[0]}")
        return self._measure_distance_end
    
    @property
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        """

        Returns
        -------

        """
        return self._current_cmd_feedback_notification
    
    async def cmd_feedback_notification_set(self, notification: PORT_CMD_FEEDBACK):
        """

        Parameters
        ----------
        notification :

        Returns
        -------

        """
        if self._debug:
            print(f"{notification.m_port[0]}: PORT_CMD_FEEDBACK: ")
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x01', 'little'):
            if self._debug:
                print(f"{notification.m_port[0]}: RECEIVED CMD_STATUS: CMD STARTED "
                      f"{notification.COMMAND[len(notification.COMMAND) - 1]}")
            self._port_free.clear()
        if notification.COMMAND[len(notification.COMMAND) - 1] == int.from_bytes(b'\x0a', 'little'):
            if self._debug:
                print(f"{notification.m_port[0]}: RECEIVED CMD_STATUS: CMD FINISHED "
                      f"{notification.COMMAND[len(notification.COMMAND) - 1]}")
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
