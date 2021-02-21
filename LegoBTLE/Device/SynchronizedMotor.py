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

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.commands.downstream import CMD_VIRTUAL_PORT_SETUP
from LegoBTLE.LegoWP.commands.upstream import DEV_PORT_NOTIFICATION_RCV, DEV_PORT_VALUE
from LegoBTLE.LegoWP.types import CONNECTION_TYPE, EVENT


class SynchronizedMotor(Device, AMotor):
    
    def __init__(self,
                 name: str = 'SynchronizedMotor',
                 motor_a: SingleMotor = None,
                 motor_b: SingleMotor = None,
                 debug: bool = False):
        
        self._name = name
        self._DEV_PORT = None
        self._DEV_PORT_connected: bool = False
        self._port_notification = None
        self._motor_a = motor_a
        self._motor_b = motor_b
        self._port_value = None
        self._debug = debug
        return
    
    @property
    def is_connected(self) -> bool:
        return self._DEV_PORT_connected
    
    @property
    def first_motor(self) -> SingleMotor:
        return self._motor_a
    
    @property
    def second_motor(self) -> SingleMotor:
        return self._motor_b
    
    def VIRTUAL_PORT_SETUP(
            self,
            connect: bool = True
            ) -> CMD_VIRTUAL_PORT_SETUP:
        if connect:
            return CMD_VIRTUAL_PORT_SETUP(
                status=CONNECTION_TYPE.CONNECT,
                port_a=self.first_motor.DEV_PORT,
                port_b=self.second_motor.DEV_PORT
                )
        else:
            return CMD_VIRTUAL_PORT_SETUP(
                status=CONNECTION_TYPE.DISCONNECT,
                port=self._DEV_PORT
                )
    
    @property
    def port_notification(self) -> DEV_PORT_NOTIFICATION_RCV:
        return self._port_notification
    
    @port_notification.setter
    def port_notification(self, notification: DEV_PORT_NOTIFICATION_RCV):
        self._port_notification = notification
        if notification.m_event == EVENT.VIRTUAL_IO_ATTACHED:
            self._DEV_PORT = notification.m_port
            self._DEV_PORT_connected = True
        if notification.m_event == EVENT.IO_DETACHED:
            self._DEV_PORT = None
            self._DEV_PORT_connected = False
        return
    
    @property
    def port_value(self) -> DEV_PORT_VALUE:
        return self._port_value
