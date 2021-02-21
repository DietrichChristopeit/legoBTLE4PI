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
from LegoBTLE.Device.AMotor import AMotor
from LegoBTLE.LegoWP.commands.downstream import DownStreamMessage
from LegoBTLE.LegoWP.commands.upstream import (EXT_SERVER_MESSAGE_RCV, HUB_CMD_STATUS_RCV, HUB_PORT_NOTIFICATION_RCV,
                                               HUB_PORT_VALUE_RCV)


class SingleMotor(AMotor):
    
    def __init__(self,
                 name: str = 'SingleMotor',
                 port=b'',
                 gearRatio: float = 1.0,
                 synchronizedPart: bool = False,
                 debug: bool = False):
        self._name = name
        self._port = port
        self._gearRatio = gearRatio
        self._synchronizedPart = synchronizedPart
        self._debug = debug
        self._port_value_rcv: HUB_PORT_VALUE_RCV = HUB_PORT_VALUE_RCV(COMMAND=bytearray(b''))
        self._cmd_status_rcv: HUB_CMD_STATUS_RCV = HUB_CMD_STATUS_RCV(COMMAND=bytearray(b''))
        return
    
    @property
    def port(self) -> bytes:
        return self._port

    @property
    def port_value_RCV(self) -> HUB_PORT_VALUE_RCV:
        return self._port_value_rcv

    @property
    def gearRatio(self) -> float:
        return self._gearRatio

    @property
    async def cmd_status_RCV(self) -> HUB_CMD_STATUS_RCV:
        return self._cmd_status_rcv

    @property
    async def ext_server_message_RCV(self) -> EXT_SERVER_MESSAGE_RCV:
        pass

    @property
    def current_cmd_snd(self) -> DownStreamMessage:
        pass

    async def port_free(self) -> bool:
        pass

    @property
    async def port_notification_RCV(self) -> HUB_PORT_NOTIFICATION_RCV:
        pass

    
    
    
        
