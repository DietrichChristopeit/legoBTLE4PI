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
from enum import Enum


class MessageType(Enum):
    HUB_ATTACHED_IO = b'\x04'
    HUB_ALERT = b'\x03'
    HUB_ERROR = b'\x05'


class MessageEvent(Enum):
    DETACHED_IO = b'\x00'
    ATTACHED_IO = b'\x01'
    ATTACHED_VIRTUAL_IO = b'\x02'


class MessageErrorCodes(Enum):
    ACK = b'\x01'
    MACK = b'\x02'
    BUFFER_OVERFLOW = b'\x03'
    TIMEOUT = b'\x04'
    COMMAND_NOT_RECOGNIZED = b'\x05'
    INVALID_USE = b'\x06'
    OVERCURRENT = b'\x07'
    INTERNAL_ERROR = b'\x08'


class MessageDeviceType(Enum):
    MOTOR = b'\x0001'
    SYSTEM_TRAIN_MOTOR = b'\x0002'
    BUTTON = b'\x0005'
    LED = b'\x0008'
    VOLTAGE = b'\x0014'
    CURRENT = b'\x0015'
    PIEZO_TONE = b'\x0016'
    RGB_LIGHT = b'\x0017'
    EXTERNAL_TILT_SENSOR = b'\x0022'
    MOTION_SENSOR = b'\x0023'
    VISION_SENSOR = b'\x0025'
    EXTERNAL_MOTOR_WITH_TACHO = b'\x0026'
    INTERNAL_MOTOR_WITH_TACHO = b'\x0027'
    INTERNAL_TILT = b'\x0028'
    
    
class Message:
    """The Message class models a Message sent to the Hub as well as the feedback notification following data execution.
    """

    def __init__(self, data: bytes = b'\x00', port: int = 0xff, withFeedback: bool = True):
        """The data structure for a command which is sent to the Hub for execution.

        :param data:
            The string of bytes comprising the command.
        :param port:
            The port for which the command is issued. It is a convenience attribute, as the port is encoded
            in the commands and result notifications.
        :param withFeedback:
            TRUE: a feedback notification is requested
            FALSE: no feedback notification is requested
        """
        self._data: bytes = data
        self._port: int = port
        self._withFeedback: bool = withFeedback
        self._error: bool = True if (int.to_bytes(self._data[2], 1, 'little') ==
                                     MessageErrorCodes.COMMAND_NOT_RECOGNIZED.value) else False
        self._errorCmd = self._data[3]
        self._errorCmdRes = self._data[len(self._data) - 1]
        return

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def port(self) -> int:
        return self._port

    @property
    def withFeedback(self) -> bool:
        return self._withFeedback

    @property
    def error(self) -> bool:
        return self._error

    @property
    def errorCmd(self) -> int:
        return self._errorCmd

    @property
    def errorCmdRes(self) -> int:
        return self._errorCmdRes
