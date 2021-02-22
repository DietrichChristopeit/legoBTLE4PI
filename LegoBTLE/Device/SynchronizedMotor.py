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

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.messages.downstream import CMD_VIRTUAL_PORT_SETUP, DownStreamMessage
from LegoBTLE.LegoWP.messages.upstream import (DEV_CMD_STATUS, DEV_GENERIC_ERROR, DEV_PORT_NOTIFICATION,
                                               DEV_CURRENT_VALUE,
                                               EXT_SERVER_MESSAGE, HUB_ACTION,
                                               HUB_ATTACHED_IO)
from LegoBTLE.LegoWP.types import CONNECTION_TYPE, PORT


class SynchronizedMotor(Device, AMotor):
    
    def __init__(self,
                 name: str = 'SynchronizedMotor',
                 motor_a: PORT = None,
                 motor_b: PORT = None,
                 debug: bool = False):
        
        self._name = name
        self._DEV_PORT = None
        self._DEV_PORT_connected: bool = False
        self._port_notification = None
        self._motor_a: PORT = motor_a
        self._motor_b: PORT = motor_b
        self._current_value = None
        self._last_value = None
        self._generic_error = None
        self._hub_action = None
        self._hub_attached_io = None
        self._ext_server_message = None
        self._port_free = True
        self._cmd_status = None
        self._current_cmd = None

        self._debug = debug
        return
    
    @property
    def is_connected(self) -> bool:
        return self._DEV_PORT_connected
    
    @property
    def first_motor(self) -> bytes:
        return PORT(self._motor_a).value
    
    @property
    def second_motor(self) -> bytes:
        return PORT(self._motor_b).value
    
    def VIRTUAL_PORT_SETUP(
            self,
            connect: bool = True
            ) -> CMD_VIRTUAL_PORT_SETUP:
        
        if connect:
            vps = CMD_VIRTUAL_PORT_SETUP(
                status=CONNECTION_TYPE.CONNECT,
                port_a=PORT(self._motor_a).value,
                port_b=PORT(self._motor_b).value
                )
            self._current_cmd = vps
            return vps
        else:
            vps = CMD_VIRTUAL_PORT_SETUP(
                status=CONNECTION_TYPE.DISCONNECT,
                port=self._DEV_PORT
                )
            return vps
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION:
        raise Warning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION):
        raise Warning('NOT APPLICABLE IN SYNCHRONIZED MOTOR')
    
    @property
    def port_value(self) -> DEV_CURRENT_VALUE:
        return self._current_value

    @port_value.setter
    def port_value(self, new_value: DEV_CURRENT_VALUE):
        self._last_value = self._current_value
        self._current_value = new_value
        return
    
    @property
    def generic_error(self) -> DEV_GENERIC_ERROR:
        return self._generic_error
    
    @generic_error.setter
    def generic_error(self, error: DEV_GENERIC_ERROR):
        self._generic_error = error
        return

    @property
    def hub_action(self) -> HUB_ACTION:
        return self._hub_action

    @hub_action.setter
    def hub_action(self, action: HUB_ACTION):
        self._hub_action = action
        return

    @property
    def hub_attached_io(self) -> HUB_ATTACHED_IO:
        return self._hub_attached_io

    @hub_attached_io.setter
    def hub_attached_io(self, io: HUB_ATTACHED_IO):
        self._hub_attached_io = io
        self._DEV_PORT = io.m_port
        self._motor_a = PORT(io.m_vport_a)
        self._motor_b = PORT(io.m_vport_b)
        return

    @property
    def ext_server_message(self) -> EXT_SERVER_MESSAGE:
        return self._ext_server_message

    @ext_server_message.setter
    def ext_server_message(self, external_msg: EXT_SERVER_MESSAGE):
        self._ext_server_message = external_msg
        return

    @property
    def port_free(self) -> bool:
        return self._port_free

    @port_free.setter
    def port_free(self, status: bool):
        self._port_free = status
        return

    @property
    def cmd_status(self) -> DEV_CMD_STATUS:
        return self._cmd_status

    @cmd_status.setter
    def cmd_status(self, status: DEV_CMD_STATUS):
        self._cmd_status = status
        if self._cmd_status.m_cmd_status_str not in ('IDLE', 'EMPTY_BUF_CMD_COMPLETED'):
            self._port_free = False
        else:
            self._port_free = True
        return

    @property
    def current_cmd_snt(self) -> DownStreamMessage:
        return self._current_cmd

    @current_cmd_snt.setter
    def current_cmd_snt(self, command: DownStreamMessage):
        self._current_cmd = command
        return
