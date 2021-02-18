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

from dataclasses import dataclass


@dataclass
class D_TYPE:
    INTERNAL_MOTOR: bytes = b'\x01'
    SYSTEM_TRAIN_MOTOR: bytes = b'\x02'
    BUTTON: bytes = b'\x05'
    LED: bytes = b'\x08'
    VOLTAGE: bytes = b'\x14'
    CURRENT: bytes = b'\x15'
    PIEZO_TONE: bytes = b'\x16'
    RGB_LIGHT: bytes = b'\x17'
    EXTERNAL_TILT_SENSOR: bytes = b'\x22'
    MOTION_SENSOR: bytes = b'\x23'
    VISION_SENSOR: bytes = b'\x25'
    EXTERNAL_MOTOR: bytes = b'\x2e'
    EXTERNAL_MOTOR_WITH_TACHO: bytes = b'\x2f'
    INTERNAL_MOTOR_WITH_TACHO: bytes = b'\x27'
    INTERNAL_TILT: bytes = b'\x28'


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
    UPS_EXT_SERVER_ACTION: bytes = b'\x00'
    
    def __len__(self):
        return 1


@dataclass
class HUB_ALERT:
    LOW_V: bytes = b'\x01'
    HIGH_CURRENT: bytes = b'\x02'
    LOW_SIG_STRENGTH: bytes = b'\x03'
    OVER_PWR_COND: bytes = b'\x04'
    
    def __len__(self) -> int:
        return 1


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
    
    def __len__(self) -> int:
        return 1
