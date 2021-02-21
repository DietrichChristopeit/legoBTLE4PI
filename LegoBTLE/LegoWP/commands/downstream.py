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

from dataclasses import dataclass, field

from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import (COMMAND_STATUS, CONNECTION_TYPE, EVENT, HUB_ACTION, HUB_ALERT, HUB_ALERT_OPERATION,
                                   MOVEMENT, M_TYPE, SUB_COMMAND)


@dataclass
class DOWNSTREAM_MESSAGE_TYPE:
    handle: int = 0x0e
    pass


class DownStreamMessage:
    
    def __init__(self, data: bytearray):
        self.msg = None
        self._data: bytearray = data
        return
    
    def get_Message(self):
        
        if self._data[2] == M_TYPE.UPS_DNS_HUB_ACTION:
            return HUB_ACTION_SND()
        elif self._data[2] == M_TYPE.UPS_DNS_EXT_SERVER_CMD:
            pass
        elif self._data[2] == M_TYPE.DNS_VIRTUAL_PORT_SETUP:
            pass
        elif self._data[2] == M_TYPE.DNS_PORT_COMMAND:
            pass
        elif self._data[2] == M_TYPE.DNS_PORT_NOTIFICATION:
            pass
        elif self._data[2] == M_TYPE.UPS_DNS_DNS_HUB_ALERT:
            pass
        elif self._data[2] == M_TYPE.UPS_DNS_GENERAL_HUB_NOTIFICATIONS:
            pass
        else:
            raise TypeError


@dataclass
class EXT_SRV_CONNECT_REQ(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_EXT_SERVER_CMD)
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.subCMD = SUB_COMMAND.REG_W_SERVER
        self.COMMAND = self.header.COMMAND + self.port + self.subCMD
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND


@dataclass
class EXT_SRV_CONNECTED_SND(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_EXT_SERVER_CMD)
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + self.port + EVENT.EXT_SRV_CONNECTED
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND


@dataclass
class EXT_SRV_DISCONNECTED_SND(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_EXT_SERVER_CMD)
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + self.port + EVENT.EXT_SRV_DISCONNECTED
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND


@dataclass
class HUB_ACTION_SND(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_HUB_ACTION)
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + bytearray(self.hub_action)
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND


@dataclass
class HUB_ALERT_SND(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_DNS_HUB_ALERT)
    hub_alert: bytes = field(init=True, default=HUB_ALERT.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND


@dataclass
class PORT_NOTIFICATION_REQ(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_NOTIFICATION)
    port: bytes = field(init=True, default=b'\x00')
    hub_action: bytes = field(init=True, default=M_TYPE.UPS_DNS_HUB_ACTION)
    delta_interval: bytes = field(init=True, default=b'\x01\x00\x00\x00')
    notif_enabled: bytes = field(init=True, default=COMMAND_STATUS.ENABLED)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.port) + \
                       bytearray(self.hub_action) + \
                       bytearray(self.delta_interval) + \
                       bytearray(self.notif_enabled)
        
        self.COMMAND = bytearray(len(self.COMMAND).to_bytes(1, 'little', signed=False)) + self.COMMAND
    
    # b'\x0a\x00\x41\x00\x02\x01\x00\x00\x00\x01'


@dataclass
class CMD_START_SPEED(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    max_power_ccw: int = None
    max_power_cw: int = None
    max_power_ccw_1: int = None
    max_power_cw_1: int = None
    max_power_ccw_2: int = None
    max_power_cw_2: int = None
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.subCmd: bytes
        maxPwrEff_CCWCW: bytes
        
        if (self.max_power_ccw is None) and (self.max_power_cw is None):
            self.subCmd: bytes = SUB_COMMAND.TURN_UNLIMITED_SYNC
            maxPwrEff_CCWCW: bytes = (-1 * self.max_power_ccw_1).to_bytes(1, 'little', signed=True) + \
                                     self.max_power_cw_1.to_bytes(1, 'little', signed=False) + \
                                     (-1 * self.max_power_ccw_2).to_bytes(1, 'little', signed=True) + \
                                     self.max_power_cw_2.to_bytes(1, 'little', signed=False)
        else:
            self.subCmd: bytes = SUB_COMMAND.TURN_UNLIMITED
            maxPwrEff_CCWCW: bytes = (-1 * self.max_power_ccw).to_bytes(1, 'little', signed=True) + \
                                     self.max_power_cw.to_bytes(1, 'little', signed=False)
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       self.subCmd + \
                       maxPwrEff_CCWCW + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.profile_nr + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                 'little',
                                                                                                 signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_TIME(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    time: int = 0
    speed: int = None
    direction: MOVEMENT = field(init=True, default=MOVEMENT.FORWARD)
    speed_a: int = None
    direction_a: MOVEMENT = field(init=True, default=MOVEMENT.FORWARD)
    speed_b: int = None
    direction_b: MOVEMENT = field(init=True, default=MOVEMENT.FORWARD)
    power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.subCMD: bytes
        speedEff: bytes
        if self.speed is None:
            self.subCMD: bytes = SUB_COMMAND.TURN_FOR_TIME_SYNC
            speedEff: bytes = (self.speed_a * self.direction_a).to_bytes(1, 'little', signed=True) + \
                              (self.speed_b * self.direction_b).to_bytes(1, 'little', signed=True)
        else:
            self.subCMD: bytes = SUB_COMMAND.TURN_FOR_TIME
            speedEff: bytes = (self.speed * self.direction).to_bytes(1, 'little', signed=True)
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       self.subCMD + \
                       self.time.to_bytes(1, 'little', signed=False) + \
                       speedEff + \
                       self.power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        
        self.COMMAND = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) + self.COMMAND


@dataclass
class CMD_START_SPEED_DEGREES(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    degrees: int = 0
    speed: int = None
    speed_a: int = None
    speed_b: int = None
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.subCMD: bytes
        speedEff: bytes
        if self.speed is None:
            self.subCMD: bytes = SUB_COMMAND.TURN_FOR_DEGREES_SYNC
            speedEff: bytes = self.speed_a.to_bytes(1, 'little', signed=True) + \
                              self.speed_b.to_bytes(1, 'little', signed=True)
        else:
            self.subCMD: bytes = SUB_COMMAND.TURN_FOR_DEGREES
            speedEff: bytes = self.speed.to_bytes(1, 'little', signed=True)
        
        # tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))
        
        # tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       self.subCMD + \
                       self.degrees.to_bytes(4, 'little', signed=False) + \
                       speedEff + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_GOTO_ABS_POS(DOWNSTREAM_MESSAGE_TYPE):
    """
    Generates the command to go straight to an absolute position.
        * If the parameters abs_pos_a: int and abs_pos_b: int are provided, the absolute position can be set for two
    devices separately. The command is afterwards executed in synchronized manner for both devices.
        * If the parameters abs_pos_a and abs_pos_b are not provided the parameter abs_pos must be provided. This
        triggers command execution on the given port with one positional value for all devices atatched to the given
        port (virtual or "normal").
    """
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed: int = 0
    abs_pos: int = None
    abs_pos_a: int = None
    abs_pos_b: int = None
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        """
        Generates the command CMD_GOTO_ABS_POS in COMMAND for the given parameters.
        
        :return:
            None
        :rtype:
            None
        """
        # tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
        #               (abs(self.speed_a) + abs(self.speed_b))
        #
        # tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
        #               (abs(self.speed_a) + abs(self.speed_b))
        
        self.subCMD: bytes
        absPosEff: bytes
        
        if self.abs_pos is None:
            self.subCMD: bytes = SUB_COMMAND.GOTO_ABSOLUTE_POS_SYNC
            absPosEff: bytes = self.abs_pos_a.to_bytes(2, 'little', signed=True) + \
                               self.abs_pos_b.to_bytes(2, 'little', signed=True)
        else:
            self.subCMD: bytes = SUB_COMMAND.GOTO_ABSOLUTE_POS
            absPosEff: bytes = self.abs_pos.to_bytes(4, 'little', signed=True)
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.start_cond & self.completion_cond).to_bytes(1, 'little', signed=False) + \
                       self.subCMD + \
                       absPosEff + \
                       self.speed.to_bytes(1, 'little', signed=False) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class VIRTUAL_PORT_SETUP(DOWNSTREAM_MESSAGE_TYPE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_VIRTUAL_PORT_SETUP)
    status: bytes = field(init=True, default=CONNECTION_TYPE.CONNECT)
    port: bytes = None
    port_a: bytes = None
    port_b: bytes = None
    
    def __post_init__(self):
        
        if self.status == CONNECTION_TYPE.CONNECT:
            self.COMMAND = self.header.COMMAND + \
                           self.status + \
                           self.port_a + \
                           self.port_b
        elif self.status == CONNECTION_TYPE.DISCONNECT:
            self.COMMAND = self.header.COMMAND + \
                           self.status + \
                           self.port
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND


@dataclass
class HUB_GENERAL_NOTIFICATION_REQ(DOWNSTREAM_MESSAGE_TYPE):
    handle: int = 0x0f
    COMMAND = b'\x01\x00'
