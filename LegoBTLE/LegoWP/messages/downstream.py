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

from dataclasses import dataclass, field

from LegoBTLE.LegoWP.common_message_header import COMMON_MESSAGE_HEADER
from LegoBTLE.LegoWP.types import (
    COMMAND_STATUS, CONNECTION_STATUS, PERIPHERAL_EVENT, HUB_ACTION,
    HUB_ALERT_OP, HUB_ALERT_TYPE, MOVEMENT, MESSAGE_TYPE, HUB_SUB_COMMAND, SERVER_SUB_COMMAND
    )


@dataclass
class DOWNSTREAM_MESSAGE(BaseException):
    
    def __post_init__(self):
        self.handle: bytes = b''
        self.header: bytearray = bytearray(b'')
        self.COMMAND: bytearray = bytearray(b'')
        self.port: bytes = b'\xff'


@dataclass
class CMD_EXT_SRV_CONNECT_REQ(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD)
        self.handle: bytes = b'\x00'
        self.subCMD = SERVER_SUB_COMMAND.REG_W_SERVER
        self.COMMAND = self.header.COMMAND + self.port + self.subCMD
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_EXT_SRV_DISCONNECT_REQ(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD)
        self.handle: bytes = b'\x00'
        self.subCMD = SERVER_SUB_COMMAND.DISCONNECT_F_SERVER
        self.COMMAND = self.header.COMMAND + self.port + self.subCMD
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class EXT_SRV_CONNECTED_SND(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD)
        self.handle: bytes = b'\xff'
        self.COMMAND = self.header.COMMAND + self.port + PERIPHERAL_EVENT.EXT_SRV_CONNECTED
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class EXT_SRV_DISCONNECTED_SND(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD)
        self.handle: bytes = b'\xff'
        self.COMMAND = self.header.COMMAND + self.port + PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_HUB_ACTION_HUB_SND(DOWNSTREAM_MESSAGE):
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_HUB_ACTION)
        self.handle: bytes = b'\x0f'
        self.COMMAND = self.header.COMMAND + bytearray(self.hub_action)
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class HUB_ALERT_UPDATE_REQ(DOWNSTREAM_MESSAGE):
    hub_alert: bytes = field(init=True, default=HUB_ALERT_TYPE.LOW_V)
    
    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_HUB_ALERT)
        self.hub_alert_op: bytes = HUB_ALERT_OP.DNS_UDATE_REQUEST
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class HUB_ALERT_NOTIFICATION_REQ(DOWNSTREAM_MESSAGE):
    hub_alert: bytes = field(init=True, default=HUB_ALERT_TYPE.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OP.DNS_UPDATE_ENABLE)
    
    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.UPS_DNS_HUB_ALERT)
        self.COMMAND = self.header.COMMAND + \
                       bytearray(self.hub_alert) + \
                       bytearray(self.hub_alert_op)
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_PORT_NOTIFICATION_DEV_REQ(DOWNSTREAM_MESSAGE):
    header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_PORT_NOTIFICATION)
    port: bytes = field(init=True, default=b'\x00')
    hub_action: bytes = field(init=True, default=MESSAGE_TYPE.UPS_DNS_HUB_ACTION)
    delta_interval: bytes = field(init=True, default=b'\x01\x00\x00\x00')
    notif_enabled: bytes = field(init=True, default=COMMAND_STATUS.ENABLED)
    
    def __post_init__(self):
        self.handle: bytes = b'\x0e'
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       self.hub_action + \
                       self.delta_interval + \
                       self.notif_enabled
        
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)
    
    # b'\x0a\x00\x41\x00\x02\x01\x00\x00\x00\x01'


@dataclass
class CMD_START_MOVE_DEV(DOWNSTREAM_MESSAGE):
    synced: bool = False
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed_ccw: int = None
    speed_cw: int = None
    speed_ccw_1: int = None
    speed_cw_1: int = None
    speed_ccw_2: int = None
    speed_cw_2: int = None
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_PORT_CMD)
        self.handle: bytes = b'\x0e'
        self.subCmd: bytes
        maxPwrEff_CCWCW: bytes
        
        if self.synced:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_UNLIMITED_SYNC
            maxPwrEff_CCWCW: bytes = (-1 * self.speed_ccw_1).to_bytes(1, 'little', signed=True) + \
                                     self.speed_cw_1.to_bytes(1, 'little', signed=False) + \
                                     (-1 * self.speed_ccw_2).to_bytes(1, 'little', signed=True) + \
                                     self.speed_cw_2.to_bytes(1, 'little', signed=False)
        else:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_UNLIMITED
            maxPwrEff_CCWCW: bytes = (-1 * self.speed_ccw).to_bytes(1, 'little', signed=True) + \
                                     self.speed_cw.to_bytes(1, 'little', signed=False)
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.start_cond & self.completion_cond).to_bytes(1, 'little', signed=False) + \
                       self.subCmd + \
                       maxPwrEff_CCWCW + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.profile_nr + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                 'little',
                                                                                                 signed=False)
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_START_MOVE_DEV_TIME(DOWNSTREAM_MESSAGE):
    synced: bool = False
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
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
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_PORT_CMD)
        self.handle: bytes = b'\x0e'
        self.subCMD: bytes
        speedEff: bytes
        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_TIME_SYNC
            speedEff: bytes = (self.speed_a * self.direction_a).to_bytes(1, 'little', signed=True) + \
                              (self.speed_b * self.direction_b).to_bytes(1, 'little', signed=True)
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_TIME
            speedEff: bytes = (self.speed * self.direction).to_bytes(1, 'little', signed=True)
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.start_cond & self.completion_cond).to_bytes(1, 'little', signed=False) + \
                       self.subCMD + \
                       self.time.to_bytes(1, 'little', signed=False) + \
                       speedEff + \
                       self.power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_START_MOVE_DEV_DEGREES(DOWNSTREAM_MESSAGE):
    synced: bool = False
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
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
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_PORT_CMD)
        self.handle: bytes = b'\x0e'
        self.subCMD: bytes
        speedEff: bytes
        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_DEGREES_SYNC
            speedEff: bytes = self.speed_a.to_bytes(1, 'little', signed=True) + \
                              self.speed_b.to_bytes(1, 'little', signed=True)
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_DEGREES
            speedEff: bytes = self.speed.to_bytes(1, 'little', signed=True)
        
        # tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))
        
        # tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))
        
        self.COMMAND = self.header.COMMAND + \
                       self.port + \
                       (self.start_cond & self.completion_cond).to_bytes(1, 'little', signed=False) + \
                       self.subCMD + \
                       self.degrees.to_bytes(4, 'little', signed=False) + \
                       speedEff + \
                       self.abs_max_power.to_bytes(1, 'little', signed=False) + \
                       (self.use_profile + self.use_acc_profile + self.use_decc_profile).to_bytes(1,
                                                                                                  'little',
                                                                                                  signed=False)
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND
                                 )


@dataclass
class CMD_MOVE_DEV_ABS_POS(DOWNSTREAM_MESSAGE):
    """
    Generates the command to go straight to an absolute position.
        * If the parameters abs_pos_a: int and abs_pos_b: int are provided, the absolute position can be set for two
    devices separately. The command is afterwards executed in synchronized manner for both devices.
        * If the parameters abs_pos_a and abs_pos_b are not provided the parameter abs_pos must be provided. This
        triggers command execution on the given port with one positional value for all devices atatched to the given
        port (virtual or "normal").
    """
    synced: bool = False
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
        Generates the command CMD_MOVE_DEV_ABS_POS in COMMAND for the given parameters.
        
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
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_PORT_CMD)
        self.handle: bytes = b'\x0e'
        self.subCMD: bytes
        absPosEff: bytes
        
        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.GOTO_ABSOLUTE_POS_SYNC
            absPosEff: bytes = self.abs_pos_a.to_bytes(2, 'little', signed=True) + \
                               self.abs_pos_b.to_bytes(2, 'little', signed=True)
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.GOTO_ABSOLUTE_POS
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
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_SETUP_DEV_VIRTUAL_PORT(DOWNSTREAM_MESSAGE):
    port: bytes = None
    connectionType: bytes = field(init=True, default=CONNECTION_STATUS.CONNECT)
    port_a: bytes = None
    port_b: bytes = None
    
    def __post_init__(self):
        self.header: COMMON_MESSAGE_HEADER = COMMON_MESSAGE_HEADER(message_type=MESSAGE_TYPE.DNS_VIRTUAL_PORT_SETUP)
        self.handle: bytes = b'\x0e'
        if self.connectionType == CONNECTION_STATUS.CONNECT:
            try:
                assert self.port is None
                self.COMMAND = self.header.COMMAND + \
                               self.connectionType + \
                               self.port_a + \
                               self.port_b
            except AssertionError:
                raise
        elif self.connectionType == CONNECTION_STATUS.DISCONNECT:
            try:
                assert self.port_a is None and self.port_b is None and self.port is not None
            except AssertionError:
                print("DISCONNECTING FROM VIRTUAL PORT DOES NOT REQUIRE port_a, port_b --> ignoring")
                pass
            finally:
                self.COMMAND = self.header.COMMAND + \
                               self.connectionType + \
                               self.port
        
        self.COMMAND = bytearray(self.handle +
                                 (1 + len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                                 self.COMMAND)


@dataclass
class CMD_GENERAL_NOTIFICATION_HUB_REQ(DOWNSTREAM_MESSAGE):
    
    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.COMMAND = b'\x00'
        self.COMMAND = bytearray(
                self.handle +
                (len(self.COMMAND)).to_bytes(1, 'little', signed=False) +
                self.COMMAND
                )
