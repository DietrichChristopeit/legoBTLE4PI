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
DEVICE_TYPE_key: [bytes] = list(DEVICE_TYPE.keys())
DEVICE_TYPE_val: [bytes] = list(DEVICE_TYPE.values())


MESSAGE_TYPE = {
    b'\x01': b'SND_REQ_GENERAL_HUB_NOTIFICATIONS',
    b'\x02': b'RCV_HUB_ACTION',
    b'\x03': b'RCV_ALERT',
    b'\x04': b'RCV_DEVICE_INIT',
    b'\x05': b'RCV_ERROR',
    b'\x61': b'SND_COMMAND_SETUP_SYNC_MOTOR',
    b'\x81': b'SND_MOTOR_COMMAND',
    b'\x82': b'RCV_COMMAND_STATUS',
    b'\x45': b'RCV_DATA',
    b'\x41': b'SND_REQ_DEVICE_NOTIFICATION',
    b'\x47': b'RCV_PORT_STATUS',
    b'\x00': b'SND_SERVER_ACTION',
    b' ': b'EOM'
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
    b'\x00': b'RFR',
    b'\xff': b'DCD',
    b'\x01': b'ACK',
    b'\x02': b'MACK',
    b'\x03': b'BUFFER_OVERFLOW',
    b'\x04': b'TIMEOUT',
    b'\x05': b'COMMAND_NOT_RECOGNIZED',
    b'\x06': b'INVALID_USE',
    b'\x07': b'OVERCURRENT',
    b'\x08': b'INTERNAL_ERROR',
    b'\x0a': b'EXEC_FINISHED'
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
    b'\x0a': b'T_FOR_TIME_SYNC',
    b'\x51': b'SND_DIRECT',
    b'\x00': b'REG_W_SERVER'
    }
SUBCOMMAND_key: [bytes] = list(SUBCOMMAND.keys())
SUBCOMMAND_val: [bytes] = list(SUBCOMMAND.values())

DIRECTCOMMAND = {
        b'\x02': b'D_RESET'
        }
DIRECTCOMMAND_key: [bytes] = list(DIRECTCOMMAND.keys())
DIRECTCOMMAND_val: [bytes] = list(DIRECTCOMMAND.values())


class Message:
    """The Message class models a Message sent to the Hub as well as the feedback, i.e., the port_status, following
    command execution.
    """
 
    def __init__(self, payload: bytes = b'   '):
        """The data structure for a command which is sent to the Hub for execution.
        The entire byte sequence that comprises length, cmd op_code, cmd parameter values etc is called
        payload here.

        :param payload:
            The byte sequence comprising the command.
        """
        self._payload: bytearray = bytearray(payload + b' ')
        
        self._length: int = self._payload[0]
        self._type = MESSAGE_TYPE.get(self._payload[2].to_bytes(1, 'little', signed=False), None)
        self._return_code: bytes = b''
        self._subCommand: bytes = b''
        self._powerA: bytes = b''
        self._powerB: bytes = b''
        self._final_action: bytes = b''
        self._port_status: bytes = b''
        self._deviceType: bytes = b''
        self._directCommand: bytes = b''
        self._port: bytes = b''
        
        if self._type == b' ':
            # empty Message
            return
        
        if self._type == b'SND_SERVER_ACTION':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._subCommand: bytes = SUBCOMMAND.get(self._payload[4].to_bytes(1, 'little', signed=False), None)
            self._return_code = RETURN_CODE.get(self._payload[5].to_bytes(1, 'little', signed=False), None)
        if self._type == b'RCV_DEVICE_INIT':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._event: bytes = EVENT.get(self._payload[4].to_bytes(1, 'little', signed=False), None)
            self._deviceType: bytes = DEVICE_TYPE.get(self._payload[5].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'ALERT':
            pass
        elif self._type == b'RCV_ERROR':
            self._error_trigger_cmd: bytes = MESSAGE_TYPE.get(self._payload[3].to_bytes(1, 'little', signed=False), None)
            self._return_code: bytes = RETURN_CODE.get(self._payload[4].to_bytes(1, 'little', signed=False), None)
            self._return_code: bytes = self._payload[4:]
        elif self._type == b'RCV_COMMAND_STATUS':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._return_code: bytes = RETURN_CODE.get(self._payload[4].to_bytes(1, 'little', signed=False), None)
        elif self._type == b'RCV_DATA':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._return_code: bytes = self._payload[4:]
        elif self._type == b'SND_REQ_DEVICE_NOTIFICATION':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._port_status: bytes = STATUS.get(self._payload[self._length - 1].to_bytes(1, 'little', signed=False),
                                                  None)
            self._return_code: bytes = STATUS.get(self._payload[self._length - 1].to_bytes(1, 'little', signed=False),
                                                  None)
        elif self._type == b'SND_MOTOR_COMMAND':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._sac: bytes = self._payload[4].to_bytes(1, 'little', signed=False)
            self._subCommand: bytes = SUBCOMMAND.get(self._payload[5].to_bytes(1, 'little', signed=False), None)
            if self._subCommand == b'SND_DIRECT':
                self._directCommand = DIRECTCOMMAND.get(self._payload[6].to_bytes(1, 'little', signed=False), None)
                self._return_code: bytes = self._payload[7:]
            else:
                self._powerA: bytes = self._payload[self._length - 4].to_bytes(1, 'little', signed=False)
                self._powerB: bytes = self._payload[self._length - 3].to_bytes(1, 'little', signed=False)
                self._finalAction = M_Constants.get(self._payload[self._length - 2].to_bytes(1, 'little', signed=False),
                                                    None)
        elif self._type == b'RCV_PORT_STATUS':
            self._port: bytes = self._payload[3].to_bytes(1, 'little', signed=False)
            self._port_status: bytes = STATUS.get(self._payload[self._length - 1].to_bytes(1, 'little', signed=False),
                                                  None)
            self._return_code: bytes = STATUS.get(self._payload[self._length - 1].to_bytes(1, 'little', signed=False),
                                                  None)
        elif self._type == b'SND_COMMAND_SETUP_SYNC_MOTOR':
            self._port_1 = Port.get(self._payload[self._length - 2].to_bytes(1, 'little', signed=False))
            self._port_2 = Port.get(self._payload[self._length - 1].to_bytes(1, 'little', signed=False))
        return
    
    @property
    def payload(self) -> bytes:
        return self._payload
    
    @property
    def port(self) -> bytes:
        return self._port

    @property
    def port_status(self) -> bytes:
        return self._port_status

    @property
    def port_status_str(self) -> str:
        return STATUS_val[STATUS_key.index(self._port_status)].decode('utf-8')
 
    @property
    def m_type(self) -> bytes:
        return self._type

    @property
    def m_type_str(self) -> str:
        return MESSAGE_TYPE_val[MESSAGE_TYPE_key.index(self._type)].decode('utf-8')
       
    @property
    def return_code(self) -> bytes:
        return self._return_code

    @property
    def return_code_str(self) -> str:
        return RETURN_CODE_val[RETURN_CODE_key.index(bytes(self._return_code[0]))].decode('utf-8')
    
    @property
    def dev_type(self) -> bytes:
        return self._deviceType

    @property
    def dev_type_str(self) -> str:
        return DEVICE_TYPE_val[DEVICE_TYPE_key.index(self._deviceType)].decode('utf-8')

    @property
    def event(self) -> bytes:
        return self._event

    @property
    def event_str(self) -> str:
        return EVENT_val[EVENT_key.index(self._event)].decode('utf-8')
    
    @property
    def error_trigger_cmd(self) -> bytes:
        return self._error_trigger_cmd

    @property
    def error_trigger_cmd_str(self) -> str:
        return SUBCOMMAND_val[SUBCOMMAND_key.index(self._error_trigger_cmd)].decode('utf-8')
   
    @property
    def cmd(self) -> bytes:
        return self._subCommand

    @property
    def cmd_str(self) -> str:
        return SUBCOMMAND_val[SUBCOMMAND_key.index(self._subCommand)].decode('utf-8')

    @property
    def cmd_direct(self) -> bytes:
        return self._directCommand

    @property
    def cmd_direct_str(self) -> str:
        return DIRECTCOMMAND_val[DIRECTCOMMAND_key.index(self._directCommand)].decode('utf-8')

    @property
    def powerA(self) -> bytes:
        return self._powerA

    @property
    def powerB(self) -> bytes:
        return self._powerB
    
    @property
    def final_action(self) -> MotorConstant:
        return self._finalAction
