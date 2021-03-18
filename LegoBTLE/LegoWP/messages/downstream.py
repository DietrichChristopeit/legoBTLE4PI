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

from dataclasses import dataclass, field

import bitstring

from LegoBTLE.LegoWP.types import (
    COMMAND_STATUS, CONNECTION_STATUS, HUB_ACTION, HUB_ALERT_OP, HUB_ALERT_TYPE, HUB_SUB_COMMAND, MESSAGE_TYPE,
    MOVEMENT, PERIPHERAL_EVENT,
    PORT, SERVER_SUB_COMMAND,
    )


@dataclass
class D_COMMON_MESSAGE_HEADER:
    m_type: bytes = field(init=True)

    def __post_init__(self):
        self.hub_id: bytes = b'\x00'
        self.header: bytearray = bytearray(self.hub_id[:1] + self.m_type[:1])


@dataclass
class DOWNSTREAM_MESSAGE(BaseException):
    handle: bytes = field(init=False, default=b'\x0e')
    hub_id: bytes = field(init=False, default=b'\x00')
    COMMAND: bytearray = field(init=False)


@dataclass
class CMD_EXT_SRV_CONNECT_REQ(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True)

    def __post_init__(self):
        self.handle: bytes = b'\x00'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[:1]).header
        self.subCMD = SERVER_SUB_COMMAND.REG_W_SERVER
        if isinstance(self.port, PORT):
            self.port = self.port.value

        self.COMMAND = self.header + self.port + self.subCMD

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return

    # a: CMD_EXT_SRV_CONNECT_REQ = CMD_EXT_SRV_CONNECT_REQ(b'\x03')


@dataclass
class CMD_EXT_SRV_DISCONNECT_REQ(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')

    def __post_init__(self):
        self.handle: bytes = b'\x00'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[:1]).header
        self.subCMD = SERVER_SUB_COMMAND.DISCONNECT_F_SERVER

        self.COMMAND = self.header + self.port + self.subCMD

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class EXT_SRV_CONNECTED_SND(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')

    def __post_init__(self):
        self.handle: bytes = b'\xff'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[:1]).header

        self.COMMAND = self.header + self.port + PERIPHERAL_EVENT.EXT_SRV_CONNECTED

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class EXT_SRV_DISCONNECTED_SND(DOWNSTREAM_MESSAGE):
    port: bytes = field(init=True, default=b'')

    def __post_init__(self):
        self.handle: bytes = b'\xff'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[:1]).header

        self.COMMAND = self.header + self.port + PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class CMD_HUB_ACTION_HUB_SND(DOWNSTREAM_MESSAGE):
    hub_action: bytes = field(init=True, default=HUB_ACTION.DNS_HUB_FAST_SHUTDOWN)

    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_HUB_ACTION[:1]).header
        self.COMMAND = self.header + bytearray(self.hub_action)

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class HUB_ALERT_UPDATE_REQ(DOWNSTREAM_MESSAGE):
    hub_alert: bytes = field(init=True, default=HUB_ALERT_TYPE.LOW_V)

    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_HUB_ALERT[:1]).header
        self.hub_alert_op: bytes = HUB_ALERT_OP.DNS_UDATE_REQUEST

        self.COMMAND = bytearray(
            self.header +
            self.hub_alert +
            self.hub_alert_op
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class HUB_ALERT_NOTIFICATION_REQ(DOWNSTREAM_MESSAGE):
    hub_alert: bytes = field(init=True, default=HUB_ALERT_TYPE.LOW_V)
    hub_alert_op: bytes = field(init=True, default=HUB_ALERT_OP.DNS_UPDATE_ENABLE)

    def __post_init__(self):
        self.handle: bytes = b'\x0f'
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.UPS_DNS_HUB_ALERT[:1]).header

        self.COMMAND = bytearray(
            self.header +
            self.hub_alert +
            self.hub_alert_op
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return


@dataclass
class CMD_PORT_NOTIFICATION_DEV_REQ(DOWNSTREAM_MESSAGE):
    """Assembles the Request Message enabling value updates for a given port.
     
     
        See: https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#port-input-format-setup-single
     
     """
    port: bytes = field(init=True, default=b'\x00')
    hub_action: bytes = field(init=True, default=MESSAGE_TYPE.UPS_DNS_HUB_ACTION)
    delta_interval: bytes = field(init=True, default=b'\x01\x00\x00\x00')
    notif_enabled: bytes = field(init=True, default=COMMAND_STATUS.ENABLED)

    def __post_init__(self):
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_NOTIFICATION[:1]).header
        self.COMMAND = bytearray(self.header +
                                 self.port +
                                 self.hub_action +
                                 self.delta_interval +
                                 b'\x00' * (4 - len(self.delta_interval)) +
                                 self.notif_enabled)

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return

    # a: CMD_PORT_NOTIFICATION_DEV_REQ = CMD_PORT_NOTIFICATION_DEV_REQ(port=b'\x02', delta_interval=b'\x00')


@dataclass
class CMD_TURN_PWR_DEV(DOWNSTREAM_MESSAGE):
    """Turn motor(s) with a certain amount of power until stopped (by setting power to 0).

    Any opposing force will be countered by the motor by either turning or holding the position.
    However, abs_max_power to meet the speed setting will not be exceeded.

    The direction is solely determined by the sign(speed).
    Setting the speed to 0/127 the motor will COAST/BREAK.
    
        **NOTE: In contrast to Command CMD_TURN_SPEED_DEV the system tries to maintain the force exercised on the motor**
        **shaft, while not exceeding the maximum setting. The speed may very well vary depending on opposing forces.**
        **This is the torque**
    
    See:
        * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07
        * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed1-speed2-maxpower-useprofile-0x08

    """

    synced: bool = False
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    power: int = None
    power_1: int = None
    power_2: int = None
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE

    def __post_init__(self):
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_CMD[:1]).header

        self.subCmd: bytes
        maxPwrEff_CCWCW: bytes

        if self.synced:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_PWR_UNREGULATED_SYNC
            maxPwrEff_CCWCW: bytearray = bytearray(
                bitstring.Bits(intle=self.power_1, length=8).bytes +
                bitstring.Bits(intle=self.power_2, length=8).bytes
            )
        else:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_PWR_UNREGULATED
            maxPwrEff_CCWCW: bytearray = bytearray(
                bitstring.Bits(intle=self.power, length=8).bytes
            )

        self.COMMAND: bytearray = bytearray(
            self.header +
            self.port +
            bitstring.Bits(intle=(self.start_cond & self.completion_cond), length=8).bytes +
            self.subCmd +
            maxPwrEff_CCWCW +
            bitstring.Bits(intle=self.abs_max_power, length=8).bytes +
            bitstring.Bits(intle=(self.profile_nr + self.use_acc_profile + self.use_decc_profile),
                           length=8).bytes
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND: bytearray = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return

    # a: CMD_TURN_PWR_DEV = CMD_TURN_PWR_DEV(synced=False, power=-90, abs_max_power=100, port=b'\x03')
    # a: CMD_TURN_PWR_DEV = CMD_TURN_PWR_DEV(synced=True, power_1=-90, power_2=64, abs_max_power=100, port=b'\x03')


@dataclass
class CMD_TURN_SPEED_DEV(DOWNSTREAM_MESSAGE):
    """Turn motor(s) not exceeding abs_max_power.
    
    Any opposing force will be countered by the motor by either turning or holding the position.
    However, abs_max_power to meet the speed setting will not be exceeded.
    
    The direction is solely determined by the sign(speed).
    Setting the speed to 0 the motor will HOLD the current position without turning (actively)
    
        **NOTE: In contrast to command CMD_TURN_PWR_DEV, here the speed is the main concern.**
        **The system tries to maintain the speed (turns per second, etc.).**
    
    
    See:
        * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07
        * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed1-speed2-maxpower-useprofile-0x08
        
    """

    synced: bool = False
    port: bytes = field(init=True, default=b'\x00')
    start_cond: int = field(init=True, default=MOVEMENT.ONSTART_EXEC_IMMEDIATELY)
    completion_cond: int = field(init=True, default=MOVEMENT.ONCOMPLETION_UPDATE_STATUS)
    speed: int = None
    speed_1: int = None
    speed_2: int = None
    abs_max_power: int = 0
    profile_nr: int = 0
    use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE
    use_decc_profile: MOVEMENT = MOVEMENT.USE_DECC_PROFILE

    def __post_init__(self):
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_CMD[:1]).header

        self.subCmd: bytes
        maxPwrEff_CCWCW: bytes

        if self.synced:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_SPD_UNLIMITED_SYNC
            maxPwrEff_CCWCW: bytearray = bytearray(
                bitstring.Bits(intle=self.speed_1, length=8).bytes +
                bitstring.Bits(intle=self.speed_2, length=8).bytes
            )
        else:
            self.subCmd: bytes = HUB_SUB_COMMAND.TURN_SPD_UNLIMITED
            maxPwrEff_CCWCW: bytearray = bytearray(
                bitstring.Bits(intle=self.speed, length=8).bytes
            )

        self.COMMAND: bytearray = bytearray(
            self.header +
            self.port +
            bitstring.Bits(intle=(self.start_cond & self.completion_cond), length=8).bytes +
            self.subCmd +
            maxPwrEff_CCWCW +
            bitstring.Bits(intle=self.abs_max_power, length=8).bytes +
            bitstring.Bits(intle=(self.profile_nr + self.use_acc_profile + self.use_decc_profile),
                           length=8).bytes
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND: bytearray = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )
        return

    # a: CMD_TURN_SPEED_DEV = CMD_TURN_SPEED_DEV(synced=False, speed=-90, abs_max_power=100, port=b'\x03')
    # a: CMD_TURN_SPEED_DEV = CMD_TURN_SPEED_DEV(synced=True, speed_1=-90, speed_2=64, abs_max_power=100, port=b'\x03')


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
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_CMD[:1]).header

        self.subCMD: bytes
        speedEff: bytes
        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_TIME_SYNC
            speedEff: bytearray = bytearray(
                bitstring.Bits(intle=(self.speed_a * self.direction_a), length=8).bytes +
                bitstring.Bits(intle=(self.speed_b * self.direction_b), length=8).bytes
            )
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_TIME
            speedEff: bytearray = bytearray(
                bitstring.Bits(intle=(self.speed * self.direction), length=8).bytes
            )

        self.COMMAND = bytearray(
            self.header +
            self.port +
            bitstring.Bits(intle=(self.start_cond & self.completion_cond), length=8).bytes +
            self.subCMD +
            bitstring.Bits(intle=self.time, length=16).bytes +
            speedEff +
            bitstring.Bits(intle=self.power, length=8).bytes +
            bitstring.Bits(intle=self.on_completion, length=8).bytes +
            bitstring.Bits(intle=(self.use_profile + self.use_acc_profile + self.use_decc_profile), length=8).bytes
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(self.handle +
                                 self.m_length +
                                 self.COMMAND
                                 )
        return

    # a: CMD_START_MOVE_DEV_TIME = CMD_START_MOVE_DEV_TIME(port=b'\x03', synced=False, speed=23, time=2560, on_completion=MOVEMENT.COAST)
    # a: CMD_START_MOVE_DEV_TIME = CMD_START_MOVE_DEV_TIME(port=b'\x03', synced=True, speed_a=23, speed_b=36, time=2560, on_completion=MOVEMENT.COAST)


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
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_CMD[:1]).header

        self.subCMD: bytes
        speedEff: bytes
        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_DEGREES_SYNC
            speedEff: bytearray = bytearray(
                bitstring.Bits(intle=self.speed_a, length=8).bytes +
                bitstring.Bits(intle=self.speed_b, length=8).bytes
            )
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.TURN_FOR_DEGREES
            speedEff: bytearray = bytearray(
                bitstring.Bits(intle=self.speed, length=8).bytes
            )

        # tachoL: int = ((self.degrees * 2) * abs(self.speed_a) * sign(self.speed_a)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))

        # tachoR: int = ((self.degrees * 2) * abs(self.speed_b) * sign(self.speed_b)) / \
        #              (abs(self.speed_a) + abs(self.speed_b))

        self.COMMAND = bytearray(
            self.header +
            self.port +
            bitstring.Bits(intle=(self.start_cond & self.completion_cond), length=8).bytes +
            self.subCMD +
            bitstring.Bits(intle=self.degrees, length=32).bytes +
            speedEff +
            bitstring.Bits(intle=self.abs_max_power, length=8).bytes +
            bitstring.Bits(intle=self.on_completion, length=8).bytes +
            bitstring.Bits(intle=(self.use_profile + self.use_acc_profile + self.use_decc_profile),
                           length=8).bytes
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(self.handle +
                                 self.m_length +
                                 self.COMMAND
                                 )
        return

        # a: CMD_START_MOVE_DEV_DEGREES = CMD_START_MOVE_DEV_DEGREES(synced=False, port=b'\x05', speed=72, degrees=720, on_completion=MOVEMENT.BREAK)
        # a: CMD_START_MOVE_DEV_DEGREES = CMD_START_MOVE_DEV_DEGREES(synced=True, port=b'\x05', speed_a=72, speed_b=-15, degrees=720, on_completion=MOVEMENT.HOLD)


@dataclass
class CMD_GOTO_ABS_POS_DEV(DOWNSTREAM_MESSAGE):
    """Assembles the command to go straight to an absolute position.
    
    Assembles the command to go straight to an absolute position turning left or right is specified through sign(speed).
    
        * If the parameters abs_pos_a: int and abs_pos_b: int are provided, the absolute position can be set for two
        devices separately. The command is afterwards executed in synchronized manner for both devices.
        
        * If the parameters abs_pos_a and abs_pos_b are not provided the parameter abs_pos must be provided.This
        triggers command execution on the given port with one positional value for all devices attached to the
        given port (virtual or "normal").
        
        See:
            * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos-speed-maxpower-endstate-useprofile-0x0d
            * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos1-abspos2-speed-maxpower-endstate-useprofile-0x0e
    
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
        Generates the command CMD_GOTO_ABS_POS_DEV in data for the given parameters.
        
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
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_PORT_CMD[:1]).header

        self.subCMD: bytes
        absPosEff: bytearray

        if self.synced:
            self.subCMD: bytes = HUB_SUB_COMMAND.GOTO_ABSOLUTE_POS_SYNC
            absPosEff: bytearray = bytearray(
                bitstring.Bits(intle=self.abs_pos_a, length=16).bytes +
                bitstring.Bits(intle=self.abs_pos_b, length=16).bytes
            )
        else:
            self.subCMD: bytes = HUB_SUB_COMMAND.GOTO_ABSOLUTE_POS
            absPosEff: bytearray = bytearray(
                bitstring.Bits(intle=self.abs_pos, length=32).bytes
            )

        self.COMMAND = bytearray(
            self.header +
            self.port +
            bitstring.Bits(intle=(self.start_cond & self.completion_cond), length=8).bytes +
            self.subCMD +
            absPosEff +
            bitstring.Bits(intle=self.speed, length=8).bytes +
            bitstring.Bits(intle=self.abs_max_power, length=8).bytes +
            bitstring.Bits(intle=self.on_completion, length=8).bytes +
            bitstring.Bits(intle=(self.use_profile + self.use_acc_profile + self.use_decc_profile),
                           length=8).bytes
        )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(
            self.handle +
            self.m_length +
            self.COMMAND
        )

        return


@dataclass
class CMD_SETUP_DEV_VIRTUAL_PORT(DOWNSTREAM_MESSAGE):
    port: bytes = None
    connectionType: bytes = field(init=True, default=CONNECTION_STATUS.CONNECT)
    port_a: bytes = None
    port_b: bytes = None

    def __post_init__(self):
        self.header: bytearray = D_COMMON_MESSAGE_HEADER(MESSAGE_TYPE.DNS_VIRTUAL_PORT_SETUP[:1]).header

        if self.connectionType == CONNECTION_STATUS.CONNECT:
            self.COMMAND = bytearray(
                self.header +
                self.connectionType +
                self.port_a +
                self.port_b
            )
        elif self.connectionType == CONNECTION_STATUS.DISCONNECT:
            self.COMMAND = bytearray(
                self.header +
                self.connectionType +
                self.port
            )

        self.m_length: bytes = bitstring.Bits(intle=(1 + len(self.COMMAND)), length=8).bytes

        self.COMMAND = bytearray(self.handle +
                                 self.m_length +
                                 self.COMMAND
                                 )

        return

        # a: CMD_SETUP_DEV_VIRTUAL_PORT = CMD_SETUP_DEV_VIRTUAL_PORT(port_a=b'\x02', port_b=b'\x03', connectionType=CONNECTION_STATUS.CONNECT)
        # a: CMD_SETUP_DEV_VIRTUAL_PORT = CMD_SETUP_DEV_VIRTUAL_PORT(port=b'\x10', connectionType=CONNECTION_STATUS.DISCONNECT)


@dataclass
class CMD_GENERAL_NOTIFICATION_HUB_REQ(DOWNSTREAM_MESSAGE):
    COMMAND: bytearray = bytearray(b'\x0f\x01\x00')

    def __post_init__(self):
        print(f"I AM THE {self.__class__}")
