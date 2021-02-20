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

from LegoBTLE.LegoWP.commands.upstream import sign
from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import (COMMAND_STATUS, CONNECTION_TYPE, HUB_ACTION, HUB_ALERT, HUB_ALERT_OPERATION,
                                   MOVEMENT, M_TYPE, SUB_COMMAND)


@dataclass
class HUB_ACTION_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_HUB_ACTION)
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + bytearray(self.hub_action)
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND
    
    def __len__(self) -> int:
        return int.from_bytes(self.length, 'little', signed=False)


@dataclass
class HUB_ALERT_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.UPS_DNS_DNS_HUB_ALERT)
    hub_alert: bytes = field(init=True, default=HUB_ALERT.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OPERATION.DNS_UDATE_REQUEST)
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND
    
    def __len__(self) -> int:
        return len(self.COMMAND)


@dataclass
class PORT_NOTIFICATION_REQ:
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
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND
    
    # b'\x0a\x00\x41\x00\x02\x01\x00\x00\x00\x01'


@dataclass
class PORT_CMD_SND:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    action: bytes = field(init=True, default=SUB_COMMAND.TURN_FOR_TIME)
    duration: list[int] = field(default_factory=list)
    degrees: list[float] = field(default_factory=list)
    direction: list[int] = (MOVEMENT.FORWARD,)
    pct_power: list[float] = field(default_factory=list)
    pct_max_power: int = 50
    
    def __post_init__(self):
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       self.action
        if self.action in (SUB_COMMAND.TURN_FOR_TIME_SYNC, SUB_COMMAND.TURN_UNLIMITED_SYNC):
            temp: bytes = b''
            for i, p in enumerate(self.pct_power[1:], start=1):
                self.pct_power[i] *= self.direction[i]
                temp += int.to_bytes(int(round(self.pct_power[i])), 1, 'little', signed=True)


@dataclass
class CMD_START_SPEED:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    max_power_ccw: int = 0
    max_power_cw: int = 0
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_UNLIMITED + \
                       (-1 * self.max_power_ccw).to_bytes(1, 'little', signed=True) + \
                       self.max_power_cw.to_bytes(1, 'little', signed=False) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.profile_nr + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                 'little',
                                                                                                 signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_SYNC:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    max_power_ccw_1: int = 0
    max_power_cw_1: int = 0
    max_power_ccw_2: int = 0
    max_power_cw_2: int = 0
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_UNLIMITED_SYNC + \
                       (-1 * self.max_power_ccw_1).to_bytes(1, 'little', signed=True) + \
                       self.max_power_cw_1.to_bytes(1, 'little', signed=False) + \
                       (-1 * self.max_power_ccw_2).to_bytes(1, 'little', signed=True) + \
                       self.max_power_cw_2.to_bytes(1, 'little', signed=False) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.profile_nr + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                 'little',
                                                                                                 signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_TIME:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    time: int = 0
    speed: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_FOR_TIME + \
                       self.time.to_bytes(1, 'little', signed=False) + \
                       self.speed.to_bytes(1, 'little', signed=True) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_TIME_SYNC:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    time: int = 0
    speed_a: int = 0
    speed_b: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_FOR_TIME_SYNC + \
                       self.time.to_bytes(1, 'little', signed=False) + \
                       self.speed_a.to_bytes(1, 'little', signed=True) + \
                       self.speed_b.to_bytes(1, 'little', signed=True) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_DEGREES:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed: int = 0
    degrees: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_FOR_DEGREES + \
                       self.degrees.to_bytes(4, 'little', signed=False) + \
                       self.speed.to_bytes(1, 'little', signed=True) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_START_SPEED_DEGREES_SYNC:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    degrees: int = 0
    speed_a: int = 0
    speed_b: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
                      (abs(self.speed_a) + abs(self.speed_b))
        
        tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
                      (abs(self.speed_a) + abs(self.speed_b))
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.TURN_FOR_DEGREES_SYNC + \
                       self.degrees.to_bytes(4, 'little', signed=False) + \
                       self.speed_a.to_bytes(1, 'little', signed=True) + \
                       self.speed_b.to_bytes(1, 'little', signed=True) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_GOTO_ABS_POS:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed: int = 0
    position: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.GOTO_ABSOLUTE_POS + \
                       self.position.to_bytes(4, 'little', signed=True) + \
                       self.speed.to_bytes(1, 'little', signed=True) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class CMD_GOTO_ABS_POS_SYNC:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_PORT_COMMAND)
    port: bytes = field(init=True, default=b'\x00')
    onstart_info: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    oncompletion_info: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed: int = 0
    abs_pos_a: int = 0
    abs_pos_b: int = 0
    abs_max_power: int = 0
    on_completion: MOVEMENT = MOVEMENT.BREAK
    use_profile: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        # tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
        #               (abs(self.speed_a) + abs(self.speed_b))
        #
        # tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
        #               (abs(self.speed_a) + abs(self.speed_b))
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.onstart_info & self.oncompletion_info).to_bytes(1, 'little', signed=False) + \
                       SUB_COMMAND.GOTO_ABSOLUTE_POS_SYNC + \
                       self.abs_pos_a.to_bytes(2, 'little', signed=True) + \
                       self.abs_pos_b.to_bytes(2, 'little', signed=True) + \
                       self.speed.to_bytes(1, 'little', signed=False) + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.length: bytes = (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False)
        self.COMMAND = self.length + self.COMMAND


@dataclass
class VIRTUAL_PORT_SETUP:
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=M_TYPE.DNS_VIRTUAL_PORT_SETUP)
    status: bytes = field(init=True, default=CONNECTION_TYPE.CONNECT)
    v_port: bytes = None
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
                           self.v_port
        self.length = int.to_bytes(1 + len(self.COMMAND), 1, 'little', signed=False)
        self.COMMAND = bytearray(self.length) + self.COMMAND


@dataclass
class GENERAL_PORT_NOTIFICATEION_REQ:
    COMMAND = b'\x01\x00'
