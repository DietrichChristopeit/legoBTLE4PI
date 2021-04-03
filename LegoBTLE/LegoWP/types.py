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
# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE
import ctypes
from dataclasses import dataclass, field
from enum import Enum, IntEnum

import numpy as np


def key_name(cls, value: bytearray):
    rev = {v.default[0:1]: k for k, v in cls.__new__(cls).__dataclass_fields__.items()}
    return rev.get(bytes(value), 'NIL')


@dataclass(frozen=True, )
class DEVICE_TYPE:
    INTERNAL_MOTOR: bytes = field(init=False, default=bytes(b'\x01'))
    SYSTEM_TRAIN_MOTOR: bytes = field(init=False, default=bytes(b'\x02'))
    BUTTON: bytes = field(init=False, default=bytes(b'\x05'))
    LED: bytes = field(init=False, default=bytes(b'\x08'))
    VOLTAGE: bytes = field(init=False, default=bytes(b'\x14'))
    CURRENT: bytes = field(init=False, default=bytes(b'\x15'))
    PIEZO_TONE: bytes = field(init=False, default=bytes(b'\x16'))
    RGB_LIGHT: bytes = field(init=False, default=bytes(b'\x17'))
    EXTERNAL_TILT_SENSOR: bytes = field(init=False, default=bytes(b'\x22'))
    MOTION_SENSOR: bytes = field(init=False, default=bytes(b'\x23'))
    EXTERNAL_MOTOR: bytes = field(init=False, default=bytes(b'\x2e'))
    EXTERNAL_MOTOR_WITH_TACHO: bytes = field(init=False, default=bytes(b'\x2f'))
    INTERNAL_MOTOR_WITH_TACHO: bytes = field(init=False, default=bytes(b'\x27'))
    INTERNAL_TILT: bytes = field(init=False, default=bytes(b'\x28'))
    INTERNAL_LALLES: bytes = field(init=False, default=bytes(b'\x36'))


@dataclass(frozen=True)
class MESSAGE_TYPE:
    UPS_DNS_EXT_SERVER_CMD: bytes = field(init=False, default=b'\x5c')
    UPS_DNS_GENERAL_HUB_NOTIFICATIONS: bytes = field(init=False, default=b'\x01')
    UPS_DNS_HUB_ACTION: bytes = field(init=False, default=b'\x02')
    UPS_DNS_HUB_ALERT: bytes = field(init=False, default=b'\x03')
    UPS_HUB_ATTACHED_IO: bytes = field(init=False, default=b'\x04')
    UPS_HUB_GENERIC_ERROR: bytes = field(init=False, default=b'\x05')
    DNS_PORT_NOTIFICATION: bytes = field(init=False, default=b'\x41')
    UPS_PORT_VALUE: bytes = field(init=False, default=b'\x45')
    UPS_PORT_NOTIFICATION: bytes = field(init=False, default=b'\x47')
    DNS_VIRTUAL_PORT_SETUP: bytes = field(init=False, default=b'\x61')
    DNS_PORT_CMD: bytes = field(init=False, default=b'\x81')
    UPS_PORT_CMD_FEEDBACK: bytes = field(init=False, default=b'\x82')


@dataclass(frozen=True)
class HUB_ALERT_TYPE:
    LOW_V: bytes = field(init=False, default=b'\x01')
    HIGH_CURRENT: bytes = field(init=False, default=b'\x02')
    LOW_SIG_STRENGTH: bytes = field(init=False, default=b'\x03')
    OVER_PWR_COND: bytes = field(init=False, default=b'\x04')


@dataclass(frozen=True)
class HUB_ALERT_OP:
    DNS_UPDATE_ENABLE: bytes = field(init=False, default=b'\x01')
    DNS_UPDATE_DISABLE: bytes = field(init=False, default=b'\x02')
    DNS_UPDATE_REQUEST: bytes = field(init=False, default=b'\x03')
    UPS_UPDATE: bytes = field(init=False, default=b'\x04')


@dataclass(frozen=True)
class ALERT_STATUS:
    ALERT: bytes = field(init=False, default=b'\x00')
    OK: bytes = field(init=False, default=b'\x01')


@dataclass(frozen=True)
class HUB_ACTION:
    DNS_HUB_SWITCH_OFF: bytes = field(init=False, default=b'\x01')
    DNS_HUB_DISCONNECT: bytes = field(init=False, default=b'\x02')
    DNS_HUB_VCC_PORT_CTRL_ON: bytes = field(init=False, default=b'\x03')
    DNS_HUB_VCC_PORT_CTRL_OFF: bytes = field(init=False, default=b'\x04')
    DNS_HUB_INDICATE_BUSY_ON: bytes = field(init=False, default=b'\x05')
    DNS_HUB_INDICATE_BUSY_OFF: bytes = field(init=False, default=b'\x06')
    DNS_HUB_FAST_SHUTDOWN: bytes = field(init=False, default=b'\x2F')

    UPS_HUB_WILL_SWITCH_OFF: bytes = field(init=False, default=b'\x30')
    UPS_HUB_WILL_DISCONNECT: bytes = field(init=False, default=b'\x31')
    UPS_HUB_WILL_BOOT: bytes = field(init=False, default=b'\x32')


@dataclass(frozen=True)
class PERIPHERAL_EVENT:
    IO_DETACHED: bytes = field(init=False, default=b'\x00')
    IO_ATTACHED: bytes = field(init=False, default=b'\x01')
    VIRTUAL_IO_ATTACHED: bytes = field(init=False, default=b'\x02')

    EXT_SRV_CONNECTED: bytes = field(init=False, default=b'\x03')
    EXT_SRV_DISCONNECTED: bytes = field(init=False, default=b'\x04')
    EXT_SRV_RECV: bytes = field(init=False, default=b'\x05')


@dataclass(frozen=True, )
class SUB_COMMAND:
    START_PWR_UNREGULATED: bytes = field(init=False, default=b'\x51\x00')
    START_PWR_UNREGULATED_SYNC: bytes = field(init=False, default=b'\x51\x02')
    SET_ACC_PROFILE: bytes = field(init=False, default=b'\x05')
    SET_DEACC_PROFILE: bytes = field(init=False, default=b'\x06')
    TURN_SPD_UNLIMITED: bytes = field(init=False, default=b'\x07')
    TURN_SPD_UNLIMITED_SYNC: bytes = field(init=False, default=b'\x08')
    TURN_FOR_TIME: bytes = field(init=False, default=b'\x09')
    TURN_FOR_TIME_SYNC: bytes = field(init=False, default=b'\x0a')
    TURN_FOR_DEGREES: bytes = field(init=False, default=b'\x0b')
    TURN_FOR_DEGREES_SYNC: bytes = field(init=False, default=b'\x0c')
    GOTO_ABSOLUTE_POS: bytes = field(init=False, default=b'\x0d')
    GOTO_ABSOLUTE_POS_SYNC: bytes = field(init=False, default=b'\x0e')
    SET_VALUE_L_R: bytes = field(init=False, default=b'\x14')
    WRITE_DIRECT_MODE_DATA: bytes = field(init=False, default=b'\x51')
    WRITE_DIRECT: bytes = field(init=False, default=b'\x50')


@dataclass(frozen=True)
class SERVER_SUB_COMMAND:
    REG_W_SERVER: bytes = field(init=False, default=b'\x00')
    DISCONNECT_F_SERVER: bytes = field(init=False, default=b'\xdd')


@dataclass(frozen=True)
class SUB_COMMAND_MODES:
    """
    Not yet done.
    """
    VALUE_SETTING: bytes = field(init=False, default=b'\x02')


c_uint8 = ctypes.c_uint8


class CMD_FEEDBACK_MSG(ctypes.LittleEndianStructure):
    _fields_ = [
        ("EMPTY_BUF_CMD_IN_PROGRESS", c_uint8, 1),
        ("EMPTY_BUF_CMD_COMPLETED", c_uint8, 1),
        ("CURRENT_CMD_DISCARDED", c_uint8, 1),
        ("IDLE", c_uint8, 1),
        ("BUSY", c_uint8, 1),
    ]


class CMD_FEEDBACK(ctypes.Union):
    _fields_ = [("MSG", CMD_FEEDBACK_MSG),
                ("asbyte", c_uint8)]


@dataclass(frozen=True)
class CMD_RETURN_CODE:
    RFR: bytes = field(init=False, default=b'\x00')
    DCD: bytes = field(init=False, default=b'\xdd')
    ACK: bytes = field(init=False, default=b'\x01')
    MACK: bytes = field(init=False, default=b'\x02')
    BUFFER_OVERFLOW: bytes = field(init=False, default=b'\x03')
    TIMEOUT: bytes = field(init=False, default=b'\x04')
    COMMAND_NOT_RECOGNIZED: bytes = field(init=False, default=b'\x05')
    INVALID_USE: bytes = field(init=False, default=b'\x06')
    OVERCURRENT: bytes = field(init=False, default=b'\x07')
    INTERNAL_ERROR: bytes = field(init=False, default=b'\x08')
    EXEC_FINISHED: bytes = field(init=False, default=b'\x0a')


@dataclass(frozen=True)
class COMMAND_STATUS:
    DISABLED: bytes = field(init=False, default=b'\x00')
    ENABLED: bytes = field(init=False, default=b'\x01')


@dataclass(frozen=True)
class WRITEDIRECT_MODE:
    SET_POSITION: bytes = field(init=False, default=b'\x02')
    SET_MOTOR_POWER: bytes = field(init=False, default=b'\x00')
    SET_LED_COLOR: bytes = field(init=False, default=b'\x00')
    SET_LED_RGB: bytes = field(init=False, default=b'\x00\x51\x01')


@dataclass(frozen=True)
class CONNECTION:
    DISCONNECT: bytes = field(init=False, default=b'\x00')
    CONNECT: bytes = field(init=False, default=b'\x01')


class MOVEMENT(IntEnum):
    FORWARD = 1
    CLOCKWISE = 1
    REVERSE = -1
    COUNTERCLOCKWISE = -1
    LEFT = -1
    RIGHT = 1
    BREAK = 0x7f
    HOLD = 0x7e
    COAST = 0x00
    NOT_USE_PROFILE = 0x00
    USE_ACC_PROFILE = 0x02
    USE_DEC_PROFILE = 0x01
    ONSTART_BUFFER_IF_NEEDED = 0x0f
    ONSTART_EXEC_IMMEDIATELY = 0x1f
    ONCOMPLETION_NO_ACTION = 0xf0
    ONCOMPLETION_UPDATE_STATUS = 0xf1


class HUB_COLOR(IntEnum):
    GREEN: int = 0x01
    YELLOW: int = 0x02
    RED: int = 0x03
    BLUE: int = 0x04
    PURPLE: int = 0x05
    LIGHTBLUE: int = 0x06
    TEAL: int = 0x07
    PINK: int = 0x08
    WHITE: int = 0x00


class PORT(Enum):
    A: bytes = b'\x00'
    B: bytes = b'\x01'
    C: bytes = b'\x02'
    D: bytes = b'\x03'
    LED: bytes = b'\x32'


@dataclass
class ECMD(object):
    name: str = 'PLAY Sequence Command'
    cmd: any = None
    args: list = field(init=True, default=None)
    kwargs: dict = field(init=True, default=None)
    wait: bool = False
    id: id = field(init=False, default=None)

    def __post_init__(self):
        self._name = self.name
        self.id = id(self)
        self._cmd = self.cmd
        self._args = self.args
        self._kwargs = self.kwargs
        self._wait = self.wait

    # async def play_cmd(self):
    #     return print(f"asyncio.create_task({self._cmd}({self._args,}, {self._kwargs}, wait={self._wait}))")


class EXPECTATION(IntEnum):
    NOT_MET = 0x00
    MET = 0x01


ALL_DONE = 1
ALL_PENDING = 2
EVERYTHING = 3


class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[90m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'


class Util:
    pass


class SI:
    DEG = np.pi / 180
    RAD = 180 / np.pi
