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
# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE

from dataclasses import dataclass
import ctypes
from enum import Enum, IntEnum


def key_name(cls, value: bytes):
    for i in cls.__dict__.items():
        if i[1] == value:
            return i[0]
    return 'UNKNOWN'


@dataclass
class D_TYPE:
    INTERNAL_MOTOR: bytes = b'\x00\x01'
    SYSTEM_TRAIN_MOTOR: bytes = b'\x00\x02'
    BUTTON: bytes = b'\x00\x05'
    LED: bytes = b'\x00\x08'
    VOLTAGE: bytes = b'\x00\x14'
    CURRENT: bytes = b'\x00\x15'
    PIEZO_TONE: bytes = b'\x00\x16'
    RGB_LIGHT: bytes = b'\x00\x17'
    EXTERNAL_TILT_SENSOR: bytes = b'\x00\x22'
    MOTION_SENSOR: bytes = b'\x00\x23'
    VISION_SENSOR: bytes = b'\x00\x25'
    EXTERNAL_MOTOR: bytes = b'\x00\x2e'
    EXTERNAL_MOTOR_WITH_TACHO: bytes = b'\x00\x2f'
    INTERNAL_MOTOR_WITH_TACHO: bytes = b'\x00\x27'
    INTERNAL_TILT: bytes = b'\x00\x28'


@dataclass
class M_TYPE:
    UPS_DNS_EXT_SERVER_CMD: bytes = b'\x5c'
    UPS_DNS_GENERAL_HUB_NOTIFICATIONS: bytes = b'\x01'
    UPS_DNS_HUB_ACTION: bytes = b'\x02'
    UPS_DNS_DNS_HUB_ALERT: bytes = b'\x03'
    UPS_HUB_ATTACHED_IO: bytes = b'\x04'
    UPS_HUB_GENERIC_ERROR: bytes = b'\x05'
    DNS_PORT_NOTIFICATION: bytes = b'\x41'
    UPS_PORT_VALUE: bytes = b'\x45'
    UPS_PORT_NOTIFICATION: bytes = b'\x47'
    DNS_VIRTUAL_PORT_SETUP: bytes = b'\x61'
    DNS_PORT_COMMAND: bytes = b'\x81'
    UPS_COMMAND_STATUS: bytes = b'\x82'


@dataclass
class HUB_ALERT_TYPE:
    LOW_V: bytes = b'\x01'
    HIGH_CURRENT: bytes = b'\x02'
    LOW_SIG_STRENGTH: bytes = b'\x03'
    OVER_PWR_COND: bytes = b'\x04'


@dataclass
class HUB_ALERT_OPERATION:
    DNS_UPDATE_ENABLE: bytes = b'\x01'
    DNS_UPDATE_DISABLE: bytes = b'\x02'
    DNS_UDATE_REQUEST: bytes = b'\x03'
    UPS_UDATE: bytes = b'\x04'


@dataclass
class HUB_ACTION_TYPE:
    DNS_HUB_SWITCH_OFF: bytes = b'\x01'
    DNS_HUB_DISCONNECT: bytes = b'\x02'
    DNS_HUB_VCC_PORT_CTRL_ON: bytes = b'\x03'
    DNS_HUB_VCC_PORT_CTRL_OFF: bytes = b'\x04'
    DNS_HUB_INDICATE_BUSY_ON: bytes = b'\x05'
    DNS_HUB_INDICATE_BUSY_OFF: bytes = b'\x06'
    DNS_HUB_FAST_SHUTDOWN: bytes = b'\x2F'
    
    UPS_HUB_WILL_SWITCH_OFF: bytes = b'\x30'
    UPS_HUB_WILL_DISCONNECT: bytes = b'\x31'
    UPS_HUB_WILL_BOOT: bytes = b'\x32'


@dataclass
class EVENT_TYPE:
    IO_DETACHED: bytes = b'\x00'
    IO_ATTACHED: bytes = b'\x01'
    VIRTUAL_IO_ATTACHED: bytes = b'\x02'
    
    EXT_SRV_CONNECTED: bytes = b'\x03'
    EXT_SRV_DISCONNECTED: bytes = b'\x04'


@dataclass
class SUB_COMMAND_TYPE:
    TURN_UNREGULATED: bytes = b'\x01'
    TURN_UNREGULATED_SYNC: bytes = b'\x02'
    SET_ACC_PROFILE: bytes = b'\x05'
    SET_DECC_PROFILE: bytes = b'\x06'
    TURN_UNLIMITED: bytes = b'\x07'
    TURN_UNLIMITED_SYNC: bytes = b'\x08'
    TURN_FOR_DEGREES: bytes = b'\x0b'
    TURN_FOR_DEGREES_SYNC: bytes = b'\x0c'
    TURN_FOR_TIME: bytes = b'\x09'
    TURN_FOR_TIME_SYNC: bytes = b'\x0a'
    GOTO_ABSOLUTE_POS: bytes = b'\x0e'
    GOTO_ABSOLUTE_POS_SYNC: bytes = b'\x0e'
    SND_DIRECT: bytes = b'\x51'
    REG_W_SERVER: bytes = b'\x00'
    DISCONNECT_F_SERVER: bytes = b'\xff'


@dataclass
class SUB_COMMAND_MODES_TYPE:
    """
    Not yet done.
    """
    VALUE_SETTING: bytes = b'\x02'


c_uint8 = ctypes.c_uint8


class CMD_FEEDBACK_MSG_TYPE(ctypes.LittleEndianStructure):
    _fields_ = [
        ("EMPTY_BUF_CMD_IN_PROGRESS", c_uint8, 1),
        ("EMPTY_BUF_CMD_COMPLETED", c_uint8, 1),
        ("CURRENT_CMD_DISCARDED", c_uint8, 1),
        ("IDLE", c_uint8, 1),
        ("BUSY", c_uint8, 1),
        ]


class CMD_FEEDBACK(ctypes.Union):
    _fields_ = [("MSG", CMD_FEEDBACK_MSG_TYPE),
                ("asbyte", c_uint8)]


@dataclass
class COMMAND_CODES_TYPE:
    RFR: bytes = b'\x00'
    DCD: bytes = b'\xff'
    ACK: bytes = b'\x01'
    MACK: bytes = b'\x02'
    BUFFER_OVERFLOW: bytes = b'\x03'
    TIMEOUT: bytes = b'\x04'
    COMMAND_NOT_RECOGNIZED: bytes = b'\x05'
    INVALID_USE: bytes = b'\x06'
    OVERCURRENT: bytes = b'\x07'
    INTERNAL_ERROR: bytes = b'\x08'
    EXEC_FINISHED: bytes = b'\x0a'


@dataclass
class COMMAND_STATUS_TYPE:
    DISABLED: bytes = b'\x00'
    ENABLED: bytes = b'\x01'


@dataclass
class CONNECTION_TYPE:
    DISCONNECT: bytes = b'\x00'
    CONNECT: bytes = b'\x01'


@dataclass
class ALERT_STATUS_TYPE:
    ALERT: bytes = b'\x00'
    OK: bytes = b'\x01'


class MOVEMENT(IntEnum):
    FORWARD = 0x01
    CLOCKWISE = 0x01
    REVERSE = 0xff
    COUNTERCLOCKWISE = 0xff
    LEFT = 0xff
    RIGHT = 0x01
    BREAK = 0x7f
    HOLD = 0x7e
    COAST = 0x00
    USE_ACC_PROFILE = 0x02
    USE_DECC_PROFILE = 0x01
    ONSTART_BUFFER_IF_NEEDED = 0x0f
    ONSTART_EXEC_IMMEDIATELY = 0x1f
    ONCOMPLETION_NO_ACTION = 0xf0
    ONCOMPLETION_UPDATE_STATUS = 0xf1


class PORT(Enum):
    A: bytes = b'\x00'
    B: bytes = b'\x01'
    C: bytes = b'\x02'
    D: bytes = b'\x03'
