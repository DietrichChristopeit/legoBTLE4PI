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
import asyncio
from abc import ABC, abstractmethod
from asyncio import Event

from typing import List, Tuple

from LegoBTLE.LegoWP.messages.downstream import (
    CMD_EXT_SRV_CONNECT_REQ, CMD_EXT_SRV_DISCONNECT_REQ,
    CMD_PORT_NOTIFICATION_DEV_REQ, DOWNSTREAM_MESSAGE,
    )
from LegoBTLE.LegoWP.messages.upstream import (
    DEV_GENERIC_ERROR_NOTIFICATION, DEV_PORT_NOTIFICATION, DEV_VALUE, EXT_SERVER_NOTIFICATION,
    HUB_ACTION_NOTIFICATION, HUB_ALERT_NOTIFICATION, HUB_ATTACHED_IO_NOTIFICATION, PORT_CMD_FEEDBACK,
    UpStreamMessageBuilder,
    )
from LegoBTLE.LegoWP.types import CMD_FEEDBACK_MSG, MESSAGE_TYPE


class Device(ABC):
    """This is the base class for all Devices in this project.
    
    The intention is to model each Device that can be attached to the (in theory any) Lego(c) Hub. Further test have to
    prove the suitability for other Hubs like Lego(c) EV3.
    
    Therefore, any Device (Thermo-Sensor, Camera etc.) should subclass from Device
    
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The friendly name of the Device.
        
        :return: The string name
    
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        A tuple holding the read and write connection to the Server Module given to each Device at instantiation.
        
        :return: tuple[StreamReader, StreamWriter]
        """
        raise NotImplementedError
    
    @connection.setter
    @abstractmethod
    def connection(self, connection: Tuple[asyncio.StreamReader, asyncio.StreamWriter]) -> None:
        """
        Sets a new connection for the device. The Device then only has the connection information and will send
        commands to the new destination.
        Beware: The device will not get not re-register at the destination AUTOMATICALLY. Registering at the
        destination must be invoked MANUALLY.
        
        :param tuple[asyncio.StreamReader, asyncio.StreamWriter] connection: The new destination information as
            (asyncio.Streamreader, asyncio.Streamwriter).
        :returns: Nothing
        :rtype None:
        
        """
        raise NotImplementedError

    @property
    def socket(self) -> int:
        """The socket information for the Device's connection.
        
        :returns: The socket nr.
        :rtype int:
        :raises ConnectionError:
        
        """
        
        try:
            return self.connection[1].get_extra_info('socket')
        except AttributeError as ae:
            raise ConnectionError(f"NO CONNECTION... {ae.args}...")
    
    @property
    @abstractmethod
    def server(self) -> Tuple[str, int]:
        """
        The Server information (host, port)
        
        :returns: The Server Information.
        :rtype: tuple[str, int]
        """
        raise NotImplementedError

    @property
    def host(self) -> str:
        """
        For convenience, the host part alone.
        
        :returns: The host part.
        :rtype: str
        
        """
        return self.server[0]

    @property
    def srv_port(self) -> int:
        """
        For convenience, the server-port part alone.
        
        :returns: Server port part.
        :rtype: int
        
        """
        return self.server[1]
    
    @property
    @abstractmethod
    def port(self) -> bytes:
        """Property for the Devices's Port at the Lego(c) Hub.
        
        :returns: The Lego(c) Hub Port of the Device.
        :rtype: bytes
        
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def port_free_condition(self) -> asyncio.Condition:
        """Locking condition for when the Lego Port is not occupied.
        
        Locking condition for when the Lego Port is not occupied with command execution for this Device's Lego-Port.
        
        :returns: The locking condition.
        :rtype: Condition
        
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port_free(self) -> asyncio.Event:
        """The Event for indicating whether the Device's Lego-Hub-Port is free (Event set) or not (Event cleared).

        :returns: The port free Event.
        :rtype: Event
        
        """
        
        raise NotImplementedError
    
    @property
    @abstractmethod
    def port_value(self) -> DEV_VALUE:
        """The current value (for motors degrees (SI deg) of the Device.
        
        Setting different units can be achieved by setting the Device's capabilities (guess) -
        currently not investigated further.
        
        :returns: The current value at the Device's port.
        :rtype: DEV_VALUE
        
        """
        
        raise NotImplementedError
    
    @port_value.setter
    @abstractmethod
    def port_value(self, port_value: DEV_VALUE) -> None:
        """Sets the current value (for motors degrees (SI deg) of the Device.
        
        Setting different units can be achieved by setting the Device's capabilities (guess) - currently not investigated further.

        :returns: Setter, nothing.
        :rtype: None
        
        """
        
        raise NotImplementedError

    @property
    @abstractmethod
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        """The device's Lego-Hub-Port notification.
        
        This is the upstream Device Port Notification. Response to a PORT_NOTIFICATION_REQ.
        
        :returns: The current Port Notification.
        :rtype: DEV_PORT_NOTIFICATION
        
        """
        
        raise NotImplementedError

    @port_notification.setter
    @abstractmethod
    def port_notification(self, port_notification: DEV_PORT_NOTIFICATION) -> None:
        """
        Sets the device's Lego-Hub-Port notification as UPSTREAM_MESSAGE.
        Response to a PORT_NOTIFICATION_REQ.

        :return: Setter, Nothing
        :rtype: None
        """
        
        raise NotImplementedError

    @property
    @abstractmethod
    def port2hub_connected(self) -> asyncio.Event:
        """Event indicating if the Lego-Hub-Port is connected to the Server module.
        
        This method is currently not used.
        
        
        :return: The connection Event
        :rtype: Event
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def last_cmd_snt(self) -> DOWNSTREAM_MESSAGE:
        """Property for the last sent Command
        
        :return: The last command sent over the Connection.
        :rtype: DOWNSTREAM_MESSAGE
        
        """
        raise NotImplementedError

    @last_cmd_snt.setter
    @abstractmethod
    def last_cmd_snt(self, command: DOWNSTREAM_MESSAGE):
        """Sets the last command sent.
        
        :param command: The last command.
        :return: Setter, nothing.
        :rtype: None
        
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def last_cmd_failed(self) -> DOWNSTREAM_MESSAGE:
        raise NotImplementedError

    @last_cmd_failed.setter
    @abstractmethod
    def last_cmd_failed(self, command: DOWNSTREAM_MESSAGE):
        raise NotImplementedError

    @property
    @abstractmethod
    def hub_alert_notification(self) -> HUB_ALERT_NOTIFICATION:
        raise NotImplementedError
    
    @hub_alert_notification.setter
    def hub_alert_notification(self, hub_alert_notification: HUB_ALERT_NOTIFICATION):
        raise NotImplementedError

    @property
    @abstractmethod
    def hub_alert_notification_log(self) -> List[Tuple[float, HUB_ALERT_NOTIFICATION]]:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def ext_srv_connected(self) -> asyncio.Event:
        raise NotImplementedError
    
    @property
    def ext_srv_notification(self) -> EXT_SERVER_NOTIFICATION:
        raise NotImplementedError
    
    @ext_srv_notification.setter
    def ext_srv_notification(self, ext_srv_notification: EXT_SERVER_NOTIFICATION):
        raise NotImplementedError
    
    @property
    def ext_srv_notification_log(self) -> List[Tuple[float, EXT_SERVER_NOTIFICATION]]:
        raise NotImplementedError
    
    async def connect_srv(self) -> bool:
        """Connect the Device (anything that subclasses from Device) to the Devices Command sending Server.
        
        The method starts with sending a Connect Request and upon acknowledgement constantly listens for Messages
        from the Server.

        This method is a coroutine.
        
        :return: Boolean, indicating if connection to Server could be established or not.
        :rtype: bool
        
        """
        
        current_command = CMD_EXT_SRV_CONNECT_REQ(port=self.port)
        print(f"CONNECT_REQ: {current_command.COMMAND.hex()}")
        async with self.port_free_condition:
            await self.port_free_condition.wait_for(lambda: self.port_free.is_set())
            self.port_free.clear()
            s = await self.cmd_send(current_command)
            
            self.port_free.set()
            self.port_free_condition.notify_all()
        return s
    
    async def EXT_SRV_DISCONNECT_REQ(self) -> bool:
        """Send a request for disconnection to the Server.
        
        This method is a coroutine.
        
        :returns: Flag indicating success/failure.
        :rtype: bool
        
        """
        
        current_command = CMD_EXT_SRV_DISCONNECT_REQ(port=self.port)

        async with self.port_free_condition:
            await self.port_free_condition.wait_for(lambda: self.port_free.is_set())
            self.port_free.clear()
            s = await self.cmd_send(current_command)
            self.port_free.set()
            self.port_free_condition.notify_all()
        return s

    async def REQ_PORT_NOTIFICATION(self) -> bool:
        """Request to receive notifications for the Device's Port.
        
        If not executed, the Device will not receive automatic Notifications (like Port Value etc.).
        Such Notifications would have in such a case to be requested individually.
        
        This method is a coroutine.
        
        :returns: Flag indicating success/failure.
        :rtype: bool
        
        """
        
        current_command = CMD_PORT_NOTIFICATION_DEV_REQ(port=self.port)
        async with self.port_free_condition:
            await self.port_free_condition.wait_for(lambda: self.port_free.is_set())
            self.port_free.clear()
            s = await self.cmd_send(current_command)
            self.last_cmd_snt = current_command
            self.port_free.set()
            self.port_free_condition.notify_all()
        return s
    
    async def EXT_SRV_CONNECT_REQ(self, host: str = '127.0.0.1', srv_port: int = 8888) -> bool:
        """Performs the actual Connection Request and does the listening to the Port afterwards.
        
        The method is modelled as data, though not entirely stringent.
        
        This method is a coroutine.
        
        :except ConnectionError:
        :raise ConnectionError: Re-raises the excepted ConnectionError
        :param str host: The host name.
        :param int srv_port: The servers port nr.
        :returns: Flag indicating success/failure.
        :rtype: bool
        
        """
        try:
            # device.notification = None
            self.ext_srv_connected.clear()
            print(
                    f"[CLIENT]-[MSG]: ATTEMPTING TO REGISTER [{self.name}:{self.port}] WITH SERVER "
                    f"[{self.server[0]}:"
                    f"{self.server[1]}]...")
            self.connection = await asyncio.open_connection(host=self.server[0], port=self.server[1])
        except ConnectionError:
            raise ConnectionError(
                    f"COULD NOT CONNECT [{self.name}:{self.port}] with [{self.server[0]}:{self.server[1]}...")
        else:
            self.ext_srv_connected.set()
            s = await self.connect_srv()
            bytesToRead: bytes = await self.connection[0].readexactly(1)  # waiting for answer from Server
            data = bytearray(await self.connection[0].readexactly(int(bytesToRead.hex(), 16)))
            print(f"[{self.name}:{self.port}]-[MSG]: RECEIVED CON_REQ ANSWER: {data.hex()}")
            self.dispatch_upstream_msg(data=data)
            await self.ext_srv_connected.wait()
            return s
    
    async def listen_srv(self) -> bool:
        """Listen to the Device's Server Port.
        
        This Method is a coroutine
        
        :return: Flag indicating success/failure.
        """
        print(f"[{self.name}:{self.port}]-[MSG]: LISTENING ON SOCKET [{self.socket}]...")
        while self.ext_srv_connected.is_set():
            try:
                bytes_to_read = await self.connection[0].readexactly(n=1)
                data = bytearray(await self.connection[0].readexactly(n=int(bytes_to_read.hex(), 16)))
            except (ConnectionError, IOError) as e:
                self.ext_srv_connected.clear()
                print(f"CONNECTION LOST... {e.args}")
                break
            else:
                print(f"[{self.name}:{self.port}]-[MSG]: RECEIVED DATA WHILE LISTENING: {data.hex()}")
                self.dispatch_upstream_msg(data)
            await asyncio.sleep(.001)
        print(f"[{self.server[0]}:{self.server[1]}]-[MSG]: CONNECTION CLOSED...")
        return False
    
    async def cmd_send(self, cmd: DOWNSTREAM_MESSAGE) -> bool:
        """Send a command downstream.
        
        This Method is a coroutine
        
        :param DOWNSTREAM_MESSAGE cmd: The command.
        :return: Flag indicating success/failure.
        :rtype: bool
        
        """
        if not self.ext_srv_connected.is_set():
            self.last_cmd_failed = cmd
            return False
        try:
            self.connection[1].write(cmd.COMMAND[:2])
            await self.connection[1].drain()
            self.connection[1].write(cmd.COMMAND[1:])
            await self.connection[1].drain()  # cmd sent
        except (AttributeError, ConnectionRefusedError) as ce:
            print(f"[{self.name}:{self.port}]-[MSG]: SENDING {cmd.COMMAND.hex()} OVER {self.socket} FAILED: {ce.args}...")
            self.last_cmd_failed = cmd
            return False
        else:
            self.last_cmd_snt = cmd
            return True
        
    def dispatch_upstream_msg(self, data: bytearray) -> bool:
        """Build an UPSTREAM_MESSAGE and dispatch.
        
        :param bytearray data: The UPSTREAM_MESSAGE.
        :raise TypeError: Raise if data doesn't match any supported UPSTREAM_MESSAGE.
        :return: Flag indicating success/failure.
        :rtype: bool
        
        """
        RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
        if RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
            self.ext_srv_notification = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_PORT_VALUE.hex(), 16):
            self.port_value = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK.hex(), 16):
            self.cmd_feedback_notification = RETURN_MESSAGE
            self.cmd_feedback_log.append(RETURN_MESSAGE)
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR.hex(), 16):
            self.error_notification = RETURN_MESSAGE
            self.error_notification_log.append(RETURN_MESSAGE)
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_PORT_NOTIFICATION.hex(), 16):
            self.port_notification = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
            self.ext_srv_notification = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_HUB_ATTACHED_IO.hex(), 16):
            self.hub_attached_io_notification = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type== int(MESSAGE_TYPE.UPS_DNS_HUB_ACTION.hex(), 16):
            self.hub_action_notification = RETURN_MESSAGE
        elif RETURN_MESSAGE.m_header.message_type == int(MESSAGE_TYPE.UPS_DNS_HUB_ALERT.hex(), 16):
            self.hub_alert_notification = RETURN_MESSAGE
            self.hub_alert_notification_log.append(RETURN_MESSAGE)
        else:
            raise TypeError(f"Cannot dispatch CMD-ANSWER FROM DEVICE: {data.hex()}...")
        return True
    
    @property
    @abstractmethod
    def error_notification(self) -> DEV_GENERIC_ERROR_NOTIFICATION:
        """
        Contains the current notification for a Lego-Hub-Error.
        
        :return: The ERROR-Notification
        """
        raise NotImplementedError
    
    @error_notification.setter
    @abstractmethod
    def error_notification(self, error: DEV_GENERIC_ERROR_NOTIFICATION) -> None:
        """
        Sets a Lego-Hub-ERROR_NOTIFICATION.
        
        :param error: The Lego-Hub-ERROR_NOTIFICATION.
        :return: None
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def error_notification_log(self) -> List[Tuple[float, DEV_GENERIC_ERROR_NOTIFICATION]]:
        """
        Contains all notifications for Lego-Hub-Errors.

        :return: The list of ERROR-Notifications
        """
        raise NotImplementedError
    
    @property
    def last_error(self) -> Tuple[bytes, bytes]:
        """
        The last (current) ERROR-Message as tuple of bytes indicating the erroneous command and the status of it.
        
        :return: tuple[bytes, bytes]
        """
        if self.error_notification is not None:
            return self.error_notification.m_error_cmd, self.error_notification.m_cmd_status
        else:
            return b'', b''
    
    @property
    @abstractmethod
    def hub_action_notification(self) -> HUB_ACTION_NOTIFICATION:
        """
        Indicates what the Lego-Hub is about to do (SHUTDOWN, DISCONNECT etc.).
        
        :return: The imminent action.
        """
        raise NotImplementedError
    
    @hub_action_notification.setter
    @abstractmethod
    def hub_action_notification(self, action: HUB_ACTION_NOTIFICATION) -> None:
        """
        Sets the notification of about what the Lego-Hub is about to do (SHUTDOWN, DISCONNECT etc.).

        :return: None.
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def hub_attached_io_notification(self) -> HUB_ATTACHED_IO_NOTIFICATION:
        """
        A Lego-Hub-Notification for the status of attached Devices (ATTACHED, DETACHED, etc.)
        
        :return: The HUB_ATTACHED_IO_NOTIFICATION .
        """
        raise NotImplementedError
    
    @hub_attached_io_notification.setter
    @abstractmethod
    def hub_attached_io_notification(self, io_notification: HUB_ATTACHED_IO_NOTIFICATION) -> None:
        """
        A Lego-Hub-Notification for the status of attached Devices (ATTACHED, DETACHED, etc.)

        :return: None.
        """
        raise NotImplementedError
      
    @property
    @abstractmethod
    def cmd_feedback_notification(self) -> PORT_CMD_FEEDBACK:
        raise NotImplementedError
    
    @cmd_feedback_notification.setter
    def cmd_feedback_notification(self, notification: PORT_CMD_FEEDBACK):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def cmd_feedback_log(self) -> List[Tuple[float, CMD_FEEDBACK_MSG]]:
        """
        A log of all past Command Feedback Messages.
    
        :return: the Log
        """
        raise NotImplementedError
        
    @property
    @abstractmethod
    def debug(self) -> bool:
        raise NotImplementedError
    
    @debug.setter
    @abstractmethod
    def debug(self, debug: bool) -> None:
        raise NotImplementedError
