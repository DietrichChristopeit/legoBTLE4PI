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


class M_Type(Enum):
    HUB_ACTION = b'\x02'
    ALERT = b'\x03'
    ATTACHED_IO = b'\x04'
    ERROR = b'\x05'
    RCV_DATA = b'\x45'
    RCV_COMMAND_STATUS = b'\x82'
    RCV_PORT_STATUS = b'\x47'
    SND_COMMAND_MOTOR = b'\x41'
    SND_COMMAND_SETUP_SYNC_MOTOR = b'\x61'


class M_Connection(Enum):
    DISABLE = b'\x00'
    ENABLE = b'\x01'


class M_Event(Enum):
    DETACHED_IO = b'\x00'
    ATTACHED_IO = b'\x01'
    ATTACHED_VIRTUAL_IO = b'\x02'


class M_Code(Enum):
    ACK = EXEC_START = b'\x01'
    MACK = b'\x02'
    BUFFER_OVERFLOW = b'\x03'
    TIMEOUT = b'\x04'
    COMMAND_NOT_RECOGNIZED = b'\x05'
    INVALID_USE = b'\x06'
    OVERCURRENT = b'\x07'
    INTERNAL_ERROR = b'\x08'
    EXEC_FINISH = b'\x0a'


class M_Device(Enum):
    INTERNAL_MOTOR = b'\x01'
    SYSTEM_TRAIN_MOTOR = b'\x02'
    BUTTON = b'\x05'
    LED = b'\x08'
    VOLTAGE = b'\x14'
    CURRENT = b'\x15'
    PIEZO_TONE = b'\x16'
    RGB_LIGHT = b'\x17'
    EXTERNAL_TILT_SENSOR = b'\x22'
    VISION_SENSOR = b'\x25',
    MOTION_SENSOR = b'\x23'
    EXTERNAL_MOTOR = b'\x2e'
    EXTERNAL_MOTOR_WITH_TACHO = b'\x2f'
    INTERNAL_MOTOR_WITH_TACHO = b'\x27'
    INTERNAL_TILT = b'\x28'
    UNKNOWN = b'\xff'


DEVICE_TYPE = {
    b'\x01': M_Device.INTERNAL_MOTOR,
    b'\x02': M_Device.SYSTEM_TRAIN_MOTOR,
    b'\x05': M_Device.BUTTON,
    b'\x08': M_Device.LED,
    b'\x14': M_Device.VOLTAGE,
    b'\x15': M_Device.CURRENT,
    b'\x16': M_Device.PIEZO_TONE,
    b'\x17': M_Device.RGB_LIGHT,
    b'\x22': M_Device.EXTERNAL_TILT_SENSOR,
    b'\x23': M_Device.MOTION_SENSOR,
    b'\x25': M_Device.VISION_SENSOR,
    b'\x2e': M_Device.EXTERNAL_MOTOR,
    b'\x2f': M_Device.EXTERNAL_MOTOR_WITH_TACHO,
    b'\x27': M_Device.INTERNAL_MOTOR_WITH_TACHO,
    b'\x28': M_Device.INTERNAL_TILT
    }

MESSAGE_TYPE = {
    b'\x03': M_Type.ALERT,
    b'\x04': M_Type.ATTACHED_IO,
    b'\x05': M_Type.ERROR,
    b'\x61': M_Type.SND_COMMAND_SETUP_SYNC_MOTOR,
    b'\x82': M_Type.RCV_COMMAND_STATUS,
    b'\x45': M_Type.RCV_DATA,
    b'\x41': M_Type.SND_COMMAND_MOTOR,
    b'\x47': M_Type.RCV_PORT_STATUS
    }

STATUS = {
    b'\x00': M_Connection.DISABLE,
    b'\x01': M_Connection.ENABLE
    }

EVENT = {
    b'\x00': M_Event.DETACHED_IO,
    b'\x01': M_Event.ATTACHED_IO,
    b'\x02': M_Event.ATTACHED_VIRTUAL_IO
    }

RETURN_CODE = {
    b'\x01': M_Code.ACK,
    b'\x02': M_Code.MACK,
    b'\x03': M_Code.BUFFER_OVERFLOW,
    b'\x04': M_Code.TIMEOUT,
    b'\x05': M_Code.COMMAND_NOT_RECOGNIZED,
    b'\x06': M_Code.INVALID_USE,
    b'\x07': M_Code.OVERCURRENT,
    b'\x08': M_Code.INTERNAL_ERROR,
    b'\x0a': M_Code.EXEC_FINISH
    }


class Message:
    """The Message class models a Message sent to the Hub as well as the feedback notification following data execution.
    """
    
    def __init__(self, data: bytes = b'\x00', withFeedback: bool = True):
        """The data structure for a command which is sent to the Hub for execution.

        :param data:
            The string of bytes comprising the command.
        :param withFeedback:
            TRUE: a feedback notification is requested
            FALSE: no feedback notification is requested
        """
        self._data: bytearray = bytearray(data)
        self._withFeedback: bool = withFeedback
        
        self._type = MESSAGE_TYPE.get(bytes(self._data[2]), None)
        if self._type == M_Type.ATTACHED_IO:
            self._port: bytes = bytes(self._data[3])
            self._event = EVENT.get(bytes(self._data[4]), None)
            self._deviceType = DEVICE_TYPE.get(bytes(self._data[5]), None)
        elif self._type == M_Type.ALERT:
            pass
        elif self._type == M_Type.ERROR:
            self._trigger_cmd = MESSAGE_TYPE.get(bytes(self._data[3]))
            self._return_code = RETURN_CODE.get(bytes(self._data[4]))
        elif self._type == M_Type.RCV_COMMAND_STATUS:
            self._port: bytes = bytes(self._data[3])
            self._status = RETURN_CODE.get(bytes(self._data[4]))
        elif self._type == M_Type.RCV_DATA:
            self._port: bytes = bytes(self._data[3])
            self._value: bytes = bytes(self._data[4:])
        elif self._type == M_Type.SND_COMMAND_MOTOR:
            self._port: bytes = bytes(self._data[3])
        elif self._type == M_Type.RCV_PORT_STATUS:
            self._port: bytes = bytes(self._data[3])
        return
    
    @property
    def data(self) -> bytes:
        return self._data
    
    @property
    def port(self) -> bytes:
        return self._port
    
    @property
    def withFeedback(self) -> bool:
        return self._withFeedback
    
    @property
    def m_type(self) -> M_Type:
        return self._type
    
    @property
    def cmd_value(self) -> bytes:
        return self._value
    
    @property
    def cmd_status(self) -> M_Code:
        return self._status
    
    @property
    def dev_type(self) -> M_Device:
        return self._deviceType
    
    @property
    def event(self) -> M_Event:
        return self._event

    @property
    def trigger_cmd(self) -> M_Type:
        return self._trigger_cmd

