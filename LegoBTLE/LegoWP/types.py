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
# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE
from ctypes import c_uint8
from dataclasses import dataclass


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
    UPS_DNS_GENERAL_HUB_NOTIFICATIONS: bytes = b'\x01'
    UPS_DNS_HUB_ACTION: bytes = b'\x02'
    UPS_DNS_DNS_HUB_ALERT: bytes = b'\x03'
    UPS_HUB_ATTACHED_IO: bytes = b'\x04'
    UPS_HUB_GENERIC_ERROR: bytes = b'\x05'
    DNS_VIRTUAL_PORT_SETUP: bytes = b'\x61'
    DNS_PORT_COMMAND: bytes = b'\x81'
    UPS_COMMAND_STATUS: bytes = b'\x82'
    UPS_PORT_VALUE: bytes = b'\x45'
    DNS_PORT_NOTIFICATION: bytes = b'\x41'
    UPS_PORT_NOTIFICATION: bytes = b'\x47'
    UPS_EXT_SERVER_CMD: bytes = b'\x00'


@dataclass
class HUB_ALERT:
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
class HUB_ACTION:
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
class EVENT:
    IO_DETACHED: bytes = b'\x00'
    IO_ATTACHED: bytes = b'\x01'
    VIRTUAL_IO_ATTACHED: bytes = b'\x02'
    
    SRV_CONNECTED: bytes = b'\x03'
    SRV_DISCONNECTED: bytes = b'\x04'
    
    
@dataclass
class SUB_COMMAND:
    T_UNREGULATED: bytes = b'\x01'
    T_UNREGULATED_SYNC: bytes = b'\x02'
    P_SET_TIME_TO_FULL: bytes = b'\x05'
    P_SET_TIME_TO_ZERO: bytes = b'\x06'
    T_UNLIMITED: bytes = b'\x07'
    T_UNLIMITED_SYNC: bytes = b'\x08'
    T_FOR_DEGREES: bytes = b'\x0b'
    T_FOR_TIME: bytes = b'\x09'
    T_FOR_TIME_SYNC: bytes = b'\x0a'
    SND_DIRECT: bytes = b'\x51'
    REG_W_SERVER: bytes = b'\x00'


import ctypes
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


@dataclass
class COMMAND_CODES:
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
class COMMAND_STATUS:
    DISABLED: bytes = b'\00'
    ENABLED: bytes = b'\01'

@dataclass
class ALERT_STATUS:
    ALERT: bytes = b'\00'
    OK: bytes = b'\01'

