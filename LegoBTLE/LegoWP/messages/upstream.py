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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE
import math
from collections import defaultdict
from dataclasses import dataclass, field

import LegoBTLE
from LegoBTLE.LegoWP import types
from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import CMD_FEEDBACK, CMD_RETURN_CODE, DEVICE_TYPE, HUB_ACTION, MESSAGE_TYPE, PERIPHERAL_EVENT


class UpStreamMessageBuilder:
    
    def __init__(self, data, debug=False):
        self._data: bytearray = data
        self._header = COMMON_MESSAGE_HEADER(data[:3])
        self._debug: bool = debug
        return
    
    def build(self):
        if self._debug:
            print(
                f"[{self.__class__.__name__}]-[MSG]: DATA RECEIVED FOR PORT [{self._data[3:4].hex()}], "
                f"STARTING UPSTREAMBUILDING: "
                f"{self._data.hex()}, {self._data[2]}\r\n RAW: {self._data}\r\nMESSAGE_TYPE: {self._header.m_type}")
        if self._header.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ACTION:
            if self._debug:
                print(f"GENERATING HUB_ACTION_NOTIFICATION for PORT {self._data[3:4].hex()}")
            return HUB_ACTION_NOTIFICATION(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO:
            if self._debug:
                print(f"GENERATING HUB_ATTACHED_IO_NOTIFICATION for PORT {self._data[3:4].hex()}")
            r = HUB_ATTACHED_IO_NOTIFICATION(self._data)
            return r
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR:
            if self._debug:
                print(f"GENERATING DEV_GENERIC_ERROR_NOTIFICATION for PORT {self._data[3:4].hex()}")
            return DEV_GENERIC_ERROR_NOTIFICATION(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK:
            if self._debug:
                print(f"GENERATING PORT_CMD_FEEDBACK for PORT {self._data[3:4].hex()}")
            return PORT_CMD_FEEDBACK(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_VALUE:
            if self._debug:
                print(f"GENERATING PORT_VALUE for PORT {self._data[3:4].hex()}")
            return PORT_VALUE(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_NOTIFICATION:
            if self._debug:
                print(f"GENERATING DEV_PORT_NOTIFICATION for PORT {self._data[3:4].hex()}")
            return DEV_PORT_NOTIFICATION(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD:
            if self._data[5] == PERIPHERAL_EVENT.EXT_SRV_RECV:
                if self._debug:
                    print(f"GENERATING EXT_SERVER_CMD_ACK for PORT {self._data[3:4].hex()}")
                return EXT_SERVER_CMD_ACK(self._data)
            else:
                if self._debug:
                    print(f"GENERATING EXT_SERVER_NOTIFICATION for PORT {self._data[3:4].hex()}")
                return EXT_SERVER_NOTIFICATION(self._data)
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ALERT:
            if self._debug:
                print(f"GENERATING HUB_ALERT_NOTIFICATION for PORT {self._data[3:4].hex()}")
            return HUB_ALERT_NOTIFICATION(self._data)
        else:
            if self._debug:
                print(f"EXCEPTION TypeError PORT {self._data[3:4].hex()}")
            raise TypeError


def key_name(cls, value: bytes):
    return LegoBTLE.LegoWP.types.key_name(cls, value)


def sign(x):
    return bool(x > 0) - bool(x < 0)


@dataclass
class UPSTREAM_MESSAGE:
    pass


@dataclass
class HUB_ACTION_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_return: bytes = self.COMMAND[:-2:-1]
        self.m_return_str: str = key_name(HUB_ACTION, self.m_return)


@dataclass
class HUB_ATTACHED_IO_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):

        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: int = self.COMMAND[3]
        print(f"{self.m_port} in IO/Notification")
        self.m_io_event: bytes = self.COMMAND[4:5]
        print(f"M_io_event: {self.m_io_event}")
        print(f"Periph-EVT: {PERIPHERAL_EVENT.IO_ATTACHED}")
        if self.m_io_event == PERIPHERAL_EVENT.IO_ATTACHED:
            self.m_device_type = bytes(self.COMMAND., 'utf-8')[5]
            print(f"DEVICE: {self.m_device_type}")
            self.m_device_type_str = key_name(DEVICE_TYPE, self.m_device_type)
            print(f"DEVICE: {self.m_device_type_str}")
        if self.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED:
            self.m_vport_a: bytes = self.COMMAND[6:7]
            self.m_vport_b: bytes = self.COMMAND[7:]
        return
# bytearray(b'\x0f\x00\x04d\x016\x00\x01\x00\x00\x00\x01\x00\x00\x00')

@dataclass
class EXT_SERVER_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: int = self.COMMAND[3]
        self.m_cmd_code: bytes = self.COMMAND[4:5]
        self.m_cmd_code_str: str = key_name(MESSAGE_TYPE, self.m_cmd_code)
        self.m_event: bytes = self.COMMAND[5:6]
        self.m_event_str = key_name(PERIPHERAL_EVENT, self.m_event)
        return


@dataclass
class EXT_SERVER_CMD_ACK(EXT_SERVER_NOTIFICATION):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        
    # a: EXT_SERVER_CMD_ACK = EXT_SERVER_CMD_ACK(b'\x06\x00\x5c\x03\x01\x03')


@dataclass
class DEV_GENERIC_ERROR_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_error_cmd: bytes = self.COMMAND[3:4]
        self.m_error_cmd_str: str = key_name(MESSAGE_TYPE, self.m_error_cmd)
        self.m_cmd_status: bytes = self.COMMAND[4:5]
        self.m_cmd_status_str: str = key_name(CMD_RETURN_CODE, self.m_cmd_status)
    
    def __len__(self):
        return len(self.COMMAND)


@dataclass
class PORT_CMD_FEEDBACK(UPSTREAM_MESSAGE):
    """The  feedback message for the current running command on a port, i.e., the status of the port.
    
    See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-output-command-feedback
    
    **NOTE: ALWAYS access m_port either with type(val) = int OR int(bytevalue.hex(),16)**
    
    """
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_cmd_status = defaultdict()
        self.m_port = defaultdict()
        t = CMD_FEEDBACK()

        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port = self.COMMAND[3]
        t.asbyte = self.COMMAND[4]
        self.m_cmd_status[self.COMMAND[3]] = t.MSG
        if self.COMMAND[0] >= 0x07:
            self.m_port_a = self.COMMAND[5]
            t.asbyte = self.COMMAND[6]
            self.m_cmd_status[self.COMMAND[5]] = t.MSG
        if self.COMMAND[0] >= 0x09:
            self.m_port_b = self.COMMAND[7]
            t.asbyte = self.COMMAND[8]
            self.m_cmd_status[self.COMMAND[7]] = t.MSG
        return
    
    # a:PORT_CMD_FEEDBACK = PORT_CMD_FEEDBACK(b'\x05\x00\x82\x10\x0a')
    # a:PORT_CMD_FEEDBACK = PORT_CMD_FEEDBACK(b'\x09\x00\x82\x10\x0a\x03\x08\x02\x04')
    
    def __str__(self) -> str:
        
        def get_status_str(msg) -> str:
            if msg is None:
                return 'None'
            m_cmd_feedback = CMD_FEEDBACK()
            m_cmd_feedback.asbyte = msg
            return str((m_cmd_feedback.MSG.IDLE and 'IDLE')
                       or (m_cmd_feedback.MSG.CURRENT_CMD_DISCARDED and 'CURRENT_CMD_DISCARDED ')
                       or (m_cmd_feedback.MSG.EMPTY_BUF_CMD_COMPLETED and 'EMPTY_BUF_CMD_COMPLETED')
                       or (m_cmd_feedback.MSG.EMPTY_BUF_CMD_IN_PROGRESS and 'EMPTY_BUF_CMD_IN_PROGRESS')
                       or (m_cmd_feedback.MSG.BUSY and 'BUSY'))
        
        return ','.join([get_status_str(self.COMMAND[4]), get_status_str(self.COMMAND[6]),
                         get_status_str(self.COMMAND[8])]).strip()
    
    def __len__(self):
        return self.COMMAND[0]


@dataclass
class PORT_VALUE(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: int = self.COMMAND[3]
        self.m_port_value: float = float(int.from_bytes(self.COMMAND[4:], 'little', signed=True))
        self.m_port_value_DEG: float = self.m_port_value
        self.m_port_value_RAD: float = math.pi / 180 * self.m_port_value
        self.m_direction = sign(self.m_port_value)
    
    def get_port_value_EFF(self, gearRatio: float = 1.0) -> {float, float, float}:
        """

        :param gearRatio: The ratio between driven and driving gear tooth nr.
        :raises ZeroDivisionError:
        :return:
        :rtype: dict
        """
        if gearRatio == 0.0:
            raise ZeroDivisionError
        return dict(raw_value_EFF=self.m_port_value / gearRatio,
                    raw_vale_EFF_DEG=self.m_port_value_DEG / gearRatio,
                    raw_value_EFF_RAD=self.m_port_value_RAD / gearRatio)
    
    def __len__(self):
        return self.COMMAND[0]
    
    # a: PORT_VALUE= PORT_VALUE(b'\x08\x00\x45\x00\xf7\xee\xff\xff')
    # a: PORT_VALUE= PORT_VALUE(b'\x08\x00\x45\x00\xff\xff\xff\xff')
    # a: PORT_VALUE= PORT_VALUE(b'\x08\00\x45\x00\xd5\x02\x00\x00')


@dataclass
class DEV_PORT_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: int = self.COMMAND[3]
        self.m_type_str = key_name(types.MESSAGE_TYPE, self.m_header.m_type)
        self.m_unknown: bytes = self.COMMAND[4:5]
        self.m_unknown_str = 'MUST BE MODES. IN THIS PROJECT NOT YET IMPLEMENTED'
        self.m_status = self.COMMAND[- 1].to_bytes(1, 'little', signed=False)
        self.m_status_str = key_name(types.PERIPHERAL_EVENT, self.m_status)
    
    def __len__(self):
        return self.COMMAND[0]
    # a: DEV_PORT_NOTIFICATION = a: DEV_PORT_NOTIFICATION(b'\x0a\x00\x47\x00\x02\x01\x00\x00\x00\x01')


@dataclass
class HUB_ALERT_NOTIFICATION(UPSTREAM_MESSAGE):
    """Models the Alert Notifcation sent by the HUB.
    
    The Notification has to be subscribed to receive automatic updates via the correspondent downstream message.
    
        **NOTE: It seems the Lego(c) LegoWP description is incorrect here as to mixing up UP-/DOWNSTREAM
        descriptions**
        
            See: https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#hub-alerts
    
    """
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: int = self.COMMAND[3]
        self.hub_alert_type: bytes = self.COMMAND[3:4]
        self.hub_alert_type_str = key_name(types.HUB_ALERT_TYPE, self.hub_alert_type)
        self.hub_alert_op: bytes = self.COMMAND[4:5]
        self.hub_alert_op_str = key_name(types.HUB_ALERT_OP, self.hub_alert_op)
        self.hub_alert_status = self.COMMAND[5:6]
        self.hub_alert_status_str = key_name(types.ALERT_STATUS, self.hub_alert_status)
    
    # a: HUB_ALERT_NOTIFICATION = HUB_ALERT_NOTIFICATION(b'\x06\x00\x03\x03\x04\xff') #upstream
    # a: HUB_ALERT_NOTIFICATION = HUB_ALERT_NOTIFICATION(b'\x05\x00\x03\x02\x01') #downstream
