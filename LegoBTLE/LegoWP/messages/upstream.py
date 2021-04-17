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
"""
This module contains various classes (mostly dataclasses) that together build and distribute upstream messages received from the server.
"""

# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE
import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

import LegoBTLE
from LegoBTLE.LegoWP import types
from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import CMD_FEEDBACK, CMD_RETURN_CODE, DEVICE_TYPE, HUB_ACTION, MESSAGE_TYPE, PERIPHERAL_EVENT
from LegoBTLE.networking.prettyprint.debug import debug_info


class UpStreamMessageBuilder:
    """Generates the various Message types for returned data from the server.

    """
    def __init__(self, data, debug=False):
        self._data: bytearray = data
        self._header = COMMON_MESSAGE_HEADER(data[:3])
        self._debug: bool = debug
        self._lastBuildPort: int = -1
        return
    
    def build(self):
        debug_info(f"[{self.__class__.__name__}]-[MSG]: DATA RECEIVED FOR PORT [{self._data[3]}], "
                   f"STARTING UPSTREAMBUILDING: "
                   f"{self._data.hex()}, {self._data[2]}\r\n RAW: {self._data}\r\nMESSAGE_TYPE: {self._header.m_type.hex()}", debug=self._debug)
        if self._header.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ACTION:
            debug_info(f"GENERATING HUB_ACTION_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
            ret = HUB_ACTION_NOTIFICATION(self._data)
            self._lastBuildPort = -1
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO:
            debug_info(f"GENERATING HUB_ATTACHED_IO_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
            ret = HUB_ATTACHED_IO_NOTIFICATION(self._data)
            self._lastBuildPort = ret.m_port
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR:
            debug_info(f"GENERATING DEV_GENERIC_ERROR_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
            ret = DEV_GENERIC_ERROR_NOTIFICATION(self._data)
            self._lastBuildPort = -1
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK:
            debug_info(f"GENERATING PORT_CMD_FEEDBACK for PORT {self._data[3]}", debug=self._debug)
            ret = PORT_CMD_FEEDBACK(self._data)
            self._lastBuildPort = ret.m_port
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_VALUE:
            debug_info(f"GENERATING PORT_VALUE for PORT {self._data[3]}", debug=self._debug)
            ret = PORT_VALUE(self._data)
            self._lastBuildPort = ret.m_port
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_PORT_NOTIFICATION:
            debug_info(f"GENERATING DEV_PORT_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
            ret = DEV_PORT_NOTIFICATION(self._data)
            self._lastBuildPort = ret.m_port
            return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD:
            if self._data[-1] == PERIPHERAL_EVENT.EXT_SRV_RECV:
                debug_info(f"GENERATING EXT_SERVER_CMD_ACK for PORT {self._data[3]}", debug=self._debug)
                ret = EXT_SERVER_CMD_ACK(self._data)
                return ret
            else:
                debug_info(f"GENERATING EXT_SERVER_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
                ret = EXT_SERVER_NOTIFICATION(self._data)
                return ret
        
        elif self._header.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ALERT:
            debug_info(f"GENERATING HUB_ALERT_NOTIFICATION for PORT {self._data[3]}", debug=self._debug)
            ret = HUB_ALERT_NOTIFICATION(self._data)
            self._lastBuildPort = ret.m_port
            return ret
        else:
            debug_info(f"EXCEPTION TypeError PORT {self._data[3]}", debug=self._debug)
            pass
            
    @property
    def lastBuildPort(self) -> int:
        return self._lastBuildPort


def _key_name(cls, value: bytearray):
    return LegoBTLE.LegoWP.types.key_name(cls, value)


@dataclass
class UPSTREAM_MESSAGE:
    r"""Absolute base class for all messages of type `UPSTREAM_MESSAGE`."""
    pass


@dataclass
class HUB_ACTION_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_return = self.COMMAND[:-2:-1]
        self.m_return_str: str = _key_name(HUB_ACTION, self.m_return)


@dataclass
class HUB_ATTACHED_IO_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):

        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        self.m_io_event: bytes = self.COMMAND[4:5]
        if self.m_io_event == PERIPHERAL_EVENT.IO_ATTACHED:
            self.m_device_type = self.COMMAND[5:6]
            self.m_device_type_str = _key_name(DEVICE_TYPE, self.m_device_type)
        if self.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED:
            self.m_port_a: bytes = self.COMMAND[7:8]
            
            self.m_port_b: bytes = self.COMMAND[8:]
        return
# bytearray(b'\x0f\x00\x04d\x016\x00\x01\x00\x00\x00\x01\x00\x00\x00')


@dataclass
class EXT_SERVER_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        self.m_cmd_code = self.COMMAND[4:5]
        self.m_cmd_code_str: str = _key_name(MESSAGE_TYPE, self.m_cmd_code)
        self.m_event = self.COMMAND[5:6]
        self.m_event_str = _key_name(PERIPHERAL_EVENT, self.m_event)
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
        self.m_error_cmd = self.COMMAND[3:4]
        self.m_error_cmd_str: str = _key_name(MESSAGE_TYPE, self.m_error_cmd)
        self.m_cmd_status = self.COMMAND[4:5]
        self.m_cmd_status_str: str = _key_name(CMD_RETURN_CODE, self.m_cmd_status)
    
    def __len__(self):
        return len(self.COMMAND)


@dataclass
class PORT_CMD_FEEDBACK(UPSTREAM_MESSAGE):
    r"""The feedback message for the current running command.
    
    This dataclass disassembles the byte string sent from the hub brick as command feedback for the status
    of the currently processed command.
    
    For a detailed description consult the `LEGO Wireless Protocol 3.0.00r17 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-output-command-feedback>`_.
    """
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_cmd_status = defaultdict()
        self.m_port = defaultdict()
        fb_code = CMD_FEEDBACK()

        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        fb_code.asbyte = self.COMMAND[4]
        self.m_cmd_status[self.COMMAND[3]] = fb_code.MSG
        if self.COMMAND[0] >= 0x07:
            self.m_port_a = self.COMMAND[5]
            fb_code.asbyte = self.COMMAND[6]
            self.m_cmd_status[self.COMMAND[5]] = fb_code.MSG
        if self.COMMAND[0] >= 0x09:
            self.m_port_b = self.COMMAND[7]
            fb_code.asbyte = self.COMMAND[8]
            self.m_cmd_status[self.COMMAND[7]] = fb_code.MSG
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
    """The last reported value of the Device.
    
    Methods
    -------
    get_port_value_EFF
        Returns the port value weighted against the gear ratio.
    
    Attributes
    ----------
    COMMAND : bytearray
        The raw data of the message. It gets further dissected and assigned to individual fields.
    
    m_header : COMMON_MESSAGE_HEADER
    
    """
    
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        self.m_port_value: float = float(int.from_bytes(self.COMMAND[4:], 'little', signed=True))
        self.m_port_value_DEG: float = self.m_port_value
        self.m_port_value_RAD: float = math.pi / 180 * self.m_port_value
        self.m_direction = np.sign(self.m_port_value)
    
    def get_port_value_EFF(self, gearRatio: float = 1.0) -> defaultdict:
        """Returns the port value adjusted by the installed gear train (currently a single set is supported).
        
        Parameters
        ----------
        gearRatio : float
            The ratio between the amount of teeth of the driven and driving gear.

        Returns
        -------
        (float, float, float)
            The adjusted port values.
        """
        if gearRatio == 0.0:
            raise ZeroDivisionError
        r = defaultdict(float)
        r['raw'] = self.m_port_value / gearRatio
        r['deg'] = self.m_port_value_DEG / gearRatio
        r['rad'] = self.m_port_value_RAD / gearRatio
        return r
    
    def __len__(self):
        return self.COMMAND[0]
    
    # a: PORT_VALUE= PORT_VALUE(b'\x08\x00\x45\x00\xf7\xee\xff\xff')
    # a: PORT_VALUE= PORT_VALUE(b'\x08\x00\x45\x00\xff\xff\xff\xff')
    # a: PORT_VALUE= PORT_VALUE(b'\x08\00\x45\x00\xd5\x02\x00\x00')


@dataclass
class DEV_PORT_NOTIFICATION(UPSTREAM_MESSAGE):
    COMMAND: bytearray = field(init=True)
    
    def __post_init__(self):
        self.m_header = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        self.m_type_str = _key_name(types.MESSAGE_TYPE, self.m_header.m_type)
        self.m_unknown: bytes = self.COMMAND[4:5]
        self.m_unknown_str = 'MUST BE MODES. IN THIS PROJECT NOT YET IMPLEMENTED'
        self.m_status = self.COMMAND[-1:]
        self.m_status_str = _key_name(types.PERIPHERAL_EVENT, self.m_status)
    
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
        self.m_header = COMMON_MESSAGE_HEADER(data=self.COMMAND[:3])
        self.m_port: bytes = self.COMMAND[3:4]
        self.hub_alert_type = self.COMMAND[3:4]
        self.hub_alert_type_str = _key_name(types.HUB_ALERT_TYPE, self.hub_alert_type)
        self.hub_alert_op = self.COMMAND[4:5]
        self.hub_alert_op_str = _key_name(types.HUB_ALERT_OP, self.hub_alert_op)
        self.hub_alert_status = self.COMMAND[5:6]
        self.hub_alert_status_str = _key_name(types.ALERT_STATUS, self.hub_alert_status)
    
    # a: HUB_ALERT_NOTIFICATION = HUB_ALERT_NOTIFICATION(b'\x06\x00\x03\x03\x04\xff') #upstream
    # a: HUB_ALERT_NOTIFICATION = HUB_ALERT_NOTIFICATION(b'\x05\x00\x03\x02\x01') #downstream
