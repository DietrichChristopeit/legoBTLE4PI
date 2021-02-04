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
from LegoBTLE.Constants.MotorConstant import M_Constants, MotorConstant
from LegoBTLE.Constants.Port import Port

DEVICE_TYPE = {
    b'\x01': b'INTERNAL_MOTOR',
    b'\x02': b'SYSTEM_TRAIN_MOTOR',
    b'\x05': b'BUTTON',
    b'\x08': b'LED',
    b'\x14': b'VOLTAGE',
    b'\x15': b'CURRENT',
    b'\x16': b'PIEZO_TONE',
    b'\x17': b'RGB_LIGHT',
    b'\x22': b'EXTERNAL_TILT_SENSOR',
    b'\x23': b'MOTION_SENSOR',
    b'\x25': b'VISION_SENSOR',
    b'\x2e': b'EXTERNAL_MOTOR',
    b'\x2f': b'EXTERNAL_MOTOR_WITH_TACHO',
    b'\x27': b'INTERNAL_MOTOR_WITH_TACHO',
    b'\x28': b'INTERNAL_TILT'
    }
DEVICE_TYPE_TYPE_key: [bytes] = list(DEVICE_TYPE.keys())
DEVICE_TYPE_TYPE_val: [bytes] = list(DEVICE_TYPE.values())


MESSAGE_TYPE = {
    b'\x02': b'HUB_ACTION',
    b'\x03': b'ALERT',
    b'\x04': b'DEVICE_INIT',
    b'\x05': b'ERROR',
    b'\x61': b'SND_COMMAND_SETUP_SYNC_MOTOR',
    b'\x81': b'SND_MOTOR_COMMAND',
    b'\x82': b'RCV_COMMAND_STATUS',
    b'\x45': b'RCV_DATA',
    b'\x41': b'SND_NOTIFICATION_COMMAND',
    b'\x47': b'RCV_PORT_STATUS'
    }
MESSAGE_TYPE_key: [bytes] = list(MESSAGE_TYPE.keys())
MESSAGE_TYPE_val: [bytes] = list(MESSAGE_TYPE.values())


STATUS = {
    b'\x00': b'DISABLED',
    b'\x01': b'ENABLED'
    }
STATUS_key: [bytes] = list(STATUS.keys())
STATUS_val: [bytes] = list(STATUS.values())

EVENT = {
    b'\x00': b'IO_DETACHED',
    b'\x01': b'IO_ATTACHED',
    b'\x02': b'VIRTUAL_IO_ATTACHED'
    }
EVENT_key: [bytes] = list(EVENT.keys())
EVENT_val: [bytes] = list(EVENT.values())


RETURN_CODE = {
    b'\x01': b'ACK',
    b'\x02': b'MACK',
    b'\x03': b'BUFFER_OVERFLOW',
    b'\x04': b'TIMEOUT',
    b'\x05': b'COMMAND_NOT_RECOGNIZED',
    b'\x06': b'INVALID_USE',
    b'\x07': b'OVERCURRENT',
    b'\x08': b'INTERNAL_ERROR',
    b'\x0a': b'EXEC_FINISH'
    }
RETURN_CODE_key: [bytes] = list(RETURN_CODE.keys())
RETURN_CODE_val: [bytes] = list(RETURN_CODE.values())


SUBCOMMAND = {
    b'\x01': b'T_UNREGULATED',
    b'\x02': b'T_UNREGULATED_SYNC',
    b'\x05': b'P_SET_TIME_TO_FULL',
    b'\x06': b'P_SET_TIME_TO_ZERO',
    b'\x07': b'T_UNLIMITED',
    b'\x08': b'T_UNLIMITED_SYNC',
    b'\x0b': b'T_FOR_DEGREES',
    b'\x09': b'T_FOR_TIME',
    b'\x0a': b'T_FOR_TIME_SYNC'
    }
SUBCOMMAND_key: [bytes] = list(SUBCOMMAND.keys())
SUBCOMMAND_val: [bytes] = list(SUBCOMMAND.values())


class Message:
    """The Message class models a Message sent to the Hub as well as the feedback port_status following payload execution.
    """
 
    def __init__(self, data: bytes = b'', withFeedback: bool = True):
        """The payload structure for a command which is sent to the Hub for execution.

        :param data:
            The string of bytes comprising the command.
        :param withFeedback:
            TRUE: a feedback port_status is requested
            FALSE: no feedback port_status is requested
        """
        self._data: bytearray = bytearray(data)
        self._withFeedback: bool = withFeedback
        
        self._length: int = self._data[0]
        self._type = MESSAGE_TYPE.get(self._data[2].to_bytes(1, 'little', signed=False), None)
        self._cmd_return_value: bytes = b''
        self._subCommand: bytes = b''
        self._powerA: bytes = b''
        self._powerB: bytes = b''
        self._final_action = b''
        self._port_status = b''
        self._deviceType = b''
        
        if self._type == b'DEVICE_INIT':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._event = EVENT.get(self._data[4].to_bytes(1, 'little', signed=False), None)
            self._deviceType = DEVICE_TYPE.get(self._data[5].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'ALERT':
            pass
        elif self._type == b'ERROR':
            self._error_trigger_cmd = MESSAGE_TYPE.get(self._data[3].to_bytes(1, 'little', signed=False), None)
            self._return_code = RETURN_CODE.get(self._data[4].to_bytes(1, 'little', signed=False), None)
            self._cmd_return_value = b''
        elif self._type == b'RCV_COMMAND_STATUS':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._cmd_status = RETURN_CODE.get(self._data[4].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'RCV_DATA':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._cmd_return_value: bytes = self._data[4:]
        elif self._type == b'SND_NOTIFICATION_COMMAND':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._cmd_status = STATUS.get(self._data[self._length-1].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'SND_MOTOR_COMMAND':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._sac: bytes = self._data[4].to_bytes(1, 'little', signed=False)
            self._subCommand = SUBCOMMAND.get(self._data[5].to_bytes(1, 'little', signed=False), None)
            self._powerA = self._data[self._length - 4].to_bytes(1, 'little', signed=False)
            self._powerB = self._data[self._length - 3].to_bytes(1, 'little', signed=False)
            self._finalAction = M_Constants.get(self._data[self._length - 2].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'RCV_PORT_STATUS':
            self._port: bytes = self._data[3].to_bytes(1, 'little', signed=False)
            self._port_status = STATUS.get(self._data[self._length - 1].to_bytes(1, 'little', signed=False), None)
            self._cmd_return_value = bytes(STATUS.get(self._data[self._length - 1].to_bytes(1, 'little',
                                                                                            signed=False), None))
        elif self._type == b'SND_COMMAND_SETUP_SYNC_MOTOR':
            self._motor_1 = Port.get(self._data[self._length - 2].to_bytes(1, 'little', signed=False))
            self._motor_2 = Port.get(self._data[self._length - 1].to_bytes(1, 'little', signed=False))
        return
    
    @property
    def payload(self) -> bytes:
        return self._data
    
    @property
    def port(self) -> bytes:
        return self._port

    @property
    def port_status(self) -> bytes:
        return self._port_status
    
    @property
    def withFeedback(self) -> bool:
        return self._withFeedback
    
    @property
    def m_type(self) -> bytes:
        return self._type
    
    @property
    def cmd_return_value(self) -> bytes:
        return self._cmd_return_value
    
    @property
    def cmd_status(self) -> bytes:
        return self._cmd_status
    
    @property
    def dev_type(self) -> bytes:
        return self._deviceType
    
    @property
    def event(self) -> bytes:
        return self._event
    
    @property
    def error_trigger_cmd(self) -> bytes:
        return self._error_trigger_cmd
    
    @property
    def cmd(self) -> bytes:
        return self._subCommand
    
    @property
    def powerA(self) -> bytes:
        return self._powerA

    @property
    def powerB(self) -> bytes:
        return self._powerB
    
    @property
    def final_action(self) -> MotorConstant:
        return self._finalAction
