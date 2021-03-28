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
import asyncio
from abc import abstractmethod
from asyncio import Event, Future, sleep
from collections import defaultdict
from time import monotonic
from typing import Callable, Tuple, Union

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.messages.downstream import (
    CMD_GOTO_ABS_POS_DEV, CMD_MODE_DATA_DIRECT, CMD_SET_ACC_DEACC_PROFILE, CMD_START_MOVE_DEV_DEGREES,
    CMD_START_MOVE_DEV_TIME, CMD_START_PWR_DEV, CMD_START_SPEED_DEV, )
from LegoBTLE.LegoWP.types import MOVEMENT, SUB_COMMAND, WRITEDIRECT_MODE, bcolors


class AMotor(Device):
    
    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF(gearRatio=1.0)
    
    @property
    @abstractmethod
    def E_MOTOR_STALLED(self) -> Event:
        raise NotImplementedError

    def check_stalled_cond(self, loop, last_val, last_val_time: float = 0.0, time_to_stalled: float = None):
        if last_val_time is None:
            last_val_time = monotonic()
        # print(f"{self._name} CALLED CHECKSTALLING...")
        if self.port_value == last_val:
            if (monotonic() - last_val_time) >= time_to_stalled:
                if self.debug:
                    print(f"{self.port_value} STALLED....")
                self.E_MOTOR_STALLED.set()
                return
        elif self.port_value != last_val:
            if self.debug:
                print(f"{self.name}: OK")
            last_val = self.port_value
            last_val_time = monotonic()
        loop.call_later(time_to_stalled / 1000, self.check_stalled_cond, loop, last_val, last_val_time, time_to_stalled)
        return
    
    @property
    @abstractmethod
    def wheelDiameter(self) -> float:
        raise NotImplementedError
    
    @wheelDiameter.setter
    @abstractmethod
    def wheelDiameter(self, diameter: float = 100.0):
        """
        
        Keyword Args:
            diameter (float): The wheel diameter in mm.

        Returns:
            nothing (None):
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def gearRatio(self) -> Union[Tuple[float, float], float]:
        """
        
        :return: The gear ratios.
        :rtype: tuple[float, float]
        """
        raise NotImplementedError
    
    @gearRatio.setter
    @abstractmethod
    def gearRatio(self, gearRatio: Union[Tuple[float, float], float]) -> None:
        """Sets the gear ratio(s) for the motor(s)
        
        :param Union[Tuple[float, float], float] gearRatio:
        :return:
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def current_profile(self) -> defaultdict:
        raise NotImplementedError

    @current_profile.setter
    @abstractmethod
    def current_profile(self, profile: defaultdict):
        raise NotImplementedError

    @property
    @abstractmethod
    def acc_deacc_profiles(self) -> defaultdict:
        raise NotImplementedError

    @acc_deacc_profiles.setter
    @abstractmethod
    def acc_deacc_profiles(self, profile: defaultdict):
        raise NotImplementedError
            
    async def SET_DEACC_PROFILE(self,
                                ms_to_zero_speed: int,
                                profile_nr: int = 0,
                                result: Future = None,
                                waitUntil: Callable = None,
                                waitUntil_timeout: float = None,
                                delay_before: float = 0.0,
                                delay_after: float = 0.0
                                ):
        """
        Set the de-acceleration profile and profile number.
        
        The profile id then can be used in commands like :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`.
        
        :async:
        Args:
            delay_after (float):
            delay_before (float):
            ms_to_zero_speed (int):
            profile_nr (int):
            result (Future):
            waitUntil (Callable):
            waitUntil_timeout (float):

        Returns:
            None

        """
        if self.debug:
            print(
                f"{bcolors.WARNING}{self.name}.SET_DEACC_PROFILE AT THE GATES... {bcolors.ENDC}"
                f"{bcolors.UNDERLINE}{bcolors.OKBLUE}WAITING {bcolors.ENDC}"
                )

        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.SET_DEACC_PROFILE AT THE GATES... {bcolors.OKBLUE}"
                      f"{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED {bcolors.ENDC}"
                      )
            if self.debug:
                print(f"{bcolors.WARNING}DELAY_BEFORE / {self.name} "
                      f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                      f"{bcolors.BOLD}{bcolors.OKBLUE}START {bcolors.ENDC}"
                      )
            await sleep(delay_before)
            if self.debug:
                print(f"{bcolors.WARNING}DELAY_BEFORE / {self.name} "
                      f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                      f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE {bcolors.ENDC}"
                      )

            current_command = None
            if ms_to_zero_speed is None:
                try:
                    current_command = self.acc_deacc_profiles[profile_nr]['DEACC']
                except (TypeError, KeyError) as ke:
                    self.port_free_condition.notify_all()
                    self.port_free.set()
                    result.set_result(False)
                    result.set_exception(ke)
                    raise ke(f"SET_DEACC_PROFILE {profile_nr} not found... {ke.args}")
            else:
                current_command = CMD_SET_ACC_DEACC_PROFILE(
                    profile_type=SUB_COMMAND.SET_DEACC_PROFILE,
                    port=self.port,
                    start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                    time_to_full_zero_speed=ms_to_zero_speed,
                    profile_nr=profile_nr,
                )
                try:
                    self.acc_deacc_profiles[profile_nr]['DEACC'] = current_command
                    self.current_profile['DEACC'] = (profile_nr, current_command)
                except TypeError as te:
                    self.port_free_condition.notify_all()
                    self.port_free.set()
                    result.set_result(False)
                    result.set_exception(te)
                    raise TypeError(f"Profile id [profile_nr] is {profile_nr}... {te.args}")

            if self.debug:
                print(f"{self.name}.SET_DEACC_PROFILE SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.SET_DEACC_PROFILE SENDING COMPLETE...")
            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )
            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return
    
    async def SET_ACC_PROFILE(self,
                              ms_to_full_speed: int,
                              profile_nr: int = None,
                              result: Future = None,
                              waitUntil: Callable = None,
                              waitUntil_timeout: float = None,
                              delay_before: float = 0.0,
                              delay_after: float = 0.0,
                              ):
        """Define a Acceleration Profile and assign it an id.

        This method defines an Acceleration Profile and assigns an id.
        It saves or updates the list of Acceleration Profiles and can be used in Motor Commands like
        :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`

        Args:
            delay_after ():
            delay_before ():
            ms_to_full_speed (int): Time after which the speed has to be 100%.
            profile_nr (int): The Profile ID.
            result (Future): True/False
            waitUntil (Callable): Instructs to wait until Callable is True.
            waitUntil_timeout (float): Sets an additional timeout for waiting.

        Returns:
            None
        """
        if self.debug:
            print(
                    f"{bcolors.WARNING}{self.name}.SET_ACC_PROFILE AT THE GATES... {bcolors.ENDC}"
                    f"{bcolors.UNDERLINE}{bcolors.OKBLUE}WAITING {bcolors.ENDC}")

        async with self.port_free_condition:
            await self.port_free.wait()

            self.port_free.clear()
            
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.SET_ACC_PROFILE AT THE GATES... {bcolors.ENDC}"
                      f"{bcolors.UNDERLINE}{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED {bcolors.ENDC}")
            if delay_before is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_BEFORE / {self.name} "
                          f"{bcolors.WARNING}WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START {bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_BEFORE / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE {bcolors.ENDC}"
                          )

            current_command = None
            if ms_to_full_speed is None:
                try:
                    current_command = self.acc_deacc_profiles[profile_nr]['ACC']
                except (TypeError, KeyError) as ke:
                    self.port_free_condition.notify_all()
                    self.port_free.set()
                    result.set_result(False)
                    result.set_exception(ke)
                    raise ke(f"SET_ACC_PROFILE {profile_nr} not found... {ke.args}")
            else:
                current_command = CMD_SET_ACC_DEACC_PROFILE(
                        profile_type=SUB_COMMAND.SET_ACC_PROFILE,
                        port=self.port,
                        start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                        completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                        time_to_full_zero_speed=ms_to_full_speed,
                        profile_nr=profile_nr,
                        )
                try:
                    self.acc_deacc_profiles[profile_nr]['ACC'] = current_command
                    self.current_profile['ACC'] = (profile_nr, current_command)
                except TypeError as te:
                    self.port_free_condition.notify_all()
                    self.port_free.set()
                    result.set_result(False)
                    result.set_exception(te)
                    raise TypeError(f"Profile id [tp_id] is {profile_nr}... {te.args}")
            
            if self.debug:
                print(f"{self.name}.SET_ACC_PROFILE SENDING {current_command.COMMAND.hex()}...")
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.SET_ACC_PROFILE SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return

    async def START_POWER_UNREGULATED(self,
                                      power: int = None,
                                      direction: MOVEMENT = MOVEMENT.FORWARD,
                                      start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                      time_to_stalled: float = -1.0,
                                      result: Future = None,
                                      waitUntil: Callable = None,
                                      waitUntil_timeout: float = None,
                                      delay_before: float = None,
                                      delay_after: float = None,
                                      ):
        """
        This command puts a certain amount of Power to the Motor.
        
        The motor, or virtual motor will not start turn but is merely pre-charged. This results in a more/less forceful
        turn when the command :func: START_SPEED_UNREGULATED is sent.
        
        .. note::
            If the port to which this motor is attached is a virtual port, both motors are set to this power level.
        
        Keyword Args:
            power (int):
            direction (MOVEMENT):
            start_cond (MOVEMENT):
            time_to_stalled (float): Set the timeout after which the motor, resp. this command is deemed stalled.
            result (Future):

        
        Returns:
            None
        """
        
        if self.debug:
            print(
                f"{bcolors.WARNING}{self.name}.START_POWER_UNREGULATED AT THE GATES...{bcolors.ENDC} "
                f"{bcolors.OKBLUE}{bcolors.UNDERLINE}WAITING {bcolors.ENDC} ")
    
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
        
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.START_POWER_UNREGULATED AT THE GATES...{bcolors.ENDC} "
                      f"{bcolors.UNDERLINE}{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED{bcolors.ENDC} ")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            current_command = CMD_START_PWR_DEV(
                    synced=False,
                    port=self.port,
                    power=power,
                    direction=direction,
                    start_cond=start_cond,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS
                    )
        
            if self.debug:
                print(f"{self.name}.START_POWER_UNREGULATED SENDING {current_command.COMMAND.hex()}...")
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self.check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_POWER_UNREGULATED SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return
            
    async def START_SPEED_UNREGULATED(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed: int = None,
            abs_max_power: int = 0,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: MOVEMENT = MOVEMENT.USE_DEACC_PROFILE,
            time_to_stalled: float = -1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """Start the motor.
        
        .. note::
            If the port is a virtual port, both attached motors are started.
            Motors must actively be stopped with command STOP, a reset command or a command setting the position.
        
        .. seealso::
            https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed
            -maxpower-useprofile-0x07

        Args:
            delay_after (float): 
            delay_before (float): 
            time_to_stalled (float):
            start_cond ():
            completion_cond ():
            speed (int): The speed in percent.
            abs_max_power ():
            use_profile ():
            use_acc_profile (MOVEMENT):
            use_deacc_profile (MOVEMENT)
            result (Future): The result of the completed execution of this command.
            waitUntil (float):
            waitUntil_timeout (float):
        """
    
        if self.debug:
            print(f"{bcolors.WARNING}{self.name}.START_SPEED AT THE GATES...{bcolors.ENDC} "
                  f"{bcolors.OKBLUE}{bcolors.UNDERLINE}WAITING{bcolors.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.START_SPEED AT THE GATES...{bcolors.ENDC} "
                      f"{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED{bcolors.ENDC} ")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            current_command = CMD_START_SPEED_DEV(
                    synced=False,
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed=speed,
                    abs_max_power=abs_max_power,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile)
        
            if self.debug:
                print(f"{self.name}.START_SPEED SENDING {current_command.COMMAND.hex()}...")
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self.check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_SPEED SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return

    async def GOTO_ABS_POS(
            self,
            start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            speed=0,
            abs_pos=None,
            abs_max_power=0,
            on_completion=MOVEMENT.BREAK,
            use_profile=0,
            use_acc_profile=MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile=MOVEMENT.USE_DEACC_PROFILE,
            time_to_stalled: float = -1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """Turn the Motor to an absolute position.

        .. seealso::
            https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition
            -abspos-speed-maxpower-endstate-useprofile-0x0d

        Args:
            start_cond:
            completion_cond:
            speed:
            abs_pos:
            abs_max_power:
            on_completion:
            use_profile:
            use_acc_profile:
            use_deacc_profile:
            time_to_stalled (float):
            result ():
            waitUntil (Callable):
            waitUntil_timeout (float):
        Returns:
            Lalles (Future):

        """
    
        if self.debug:
            print(f"{bcolors.WARNING}{self.name}.GOTO_ABS_POS AT THE GATES...{bcolors.ENDC} "
                  f"{bcolors.UNDERLINE}{bcolors.OKBLUE}WAITING{bcolors.ENDC} ")

        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
        
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.GOTO_ABS_POS AT THE GATES...{bcolors.ENDC} "
                      f"{bcolors.UNDERLINE}{bcolors.UNDERLINE}{bcolors.OKBLUE}PASSED {bcolors.ENDC} ")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            current_command = CMD_GOTO_ABS_POS_DEV(
                    synced=False,
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed=speed,
                    abs_pos=abs_pos,
                    gearRatio=self.gearRatio,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile)
            if self.debug:
                print(f"{self.name}.GOTO_ABS_POS SENDING {current_command.COMMAND.hex()}...")
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self.check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.GOTO_ABS_POS SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return
    
    async def STOP(self,
                   use_profile: int = None,
                   result: Future = None,
                   waitUntil: Callable = None,
                   waitUntil_timeout: float = None,
                   delay_before: float = None,
                   delay_after: float = None,
                   ):
        """Stop the motor immediately and cancel the currently running operation.
        
        Keyword Args:
            use_profile (int): Use this profile number for stopping.
            result (Future): The result of the operation (exception or bool)
           

        Returns:
            Nothing (None): result holds the status of the command-sending command.

        """
        if use_profile is None:
            s = await self.START_SPEED_UNREGULATED(speed=0,
                                                   use_profile=self.current_profile['ACC'][0],
                                                   waitUntil=waitUntil,
                                                   waitUntil_timeout=waitUntil_timeout,
                                                   delay_before=delay_before,
                                                   delay_after=delay_after,
                                                   )
        else:
            s = await self.START_SPEED_UNREGULATED(speed=0,
                                                   use_profile=use_profile,
                                                   waitUntil=waitUntil,
                                                   waitUntil_timeout=waitUntil_timeout,
                                                   delay_before=delay_before,
                                                   delay_after=delay_after,
                                                   )
            
        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return
    
    async def SET_POSITION(self,
                           pos: int = 0,
                           result: Future = None,
                           waitUntil: Callable = None,
                           waitUntil_timeout: float = None,
                           delay_before: float = None,
                           delay_after: float = None,
                           ):
    
        if self.debug:
            print(f"{bcolors.WARNING}{self.name}.SET_POSITION AT THE GATES...{bcolors.ENDC} "
                  f"{bcolors.OKBLUE}{bcolors.UNDERLINE}WAITING{bcolors.ENDC} ")

        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{bcolors.WARNING}{self.name}.SET_POSITION AT THE GATES...{bcolors.ENDC} "
                      f"{bcolors.UNDERLINE}{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED{bcolors.ENDC} ")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            command = CMD_MODE_DATA_DIRECT(
                    port=self.port,
                    start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                    preset_mode=WRITEDIRECT_MODE.SET_POSITION,
                    motor_position=pos,
                    )
            
            if self.debug:
                print(f"{self.name}.SET_POSITION SENDING {command.COMMAND.hex()}...")
            s = await self.cmd_send(command)
            if self.debug:
                print(f"{self.name}.SET_POSITION SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()

        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return

    async def START_MOVE_DEGREES(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            degrees: int = 0,
            speed: int = None,
            abs_max_power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: MOVEMENT = MOVEMENT.USE_DEACC_PROFILE,
            time_to_stalled: float = -1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """

        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfordegrees
        -degrees-speed-maxpower-endstate-useprofile-0x0b

        Args:
            time_to_stalled ():
            start_cond (MOVEMENT):
            completion_cond (MOVEMENT):
            degrees (int):
            speed (int):
            abs_max_power (int):
            on_completion (MOVEMENT):
            use_profile (int):
            use_acc_profile (MOVEMENT):
            use_deacc_profile (MOVEMENT):
            result (Future): True if all OK, False otherwise.
            waitUntil (): If set any preceding command will not finish before this command
            waitUntil_timeout ():

        Returns:
            bool: True if no errors in cmd_send occurred, False otherwise.
            
        """
    
        if self.debug:
            print(
                    f"{bcolors.WARNING}{self.name}.START_MOVE_DEGREES{bcolors.ENDC} "
                    f"{bcolors.WARNING} AT THE GATES...{bcolors.ENDC} "
                    f"{bcolors.UNDERLINE}{bcolors.OKBLUE}WAITING{bcolors.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES AT THE GATES...{bcolors.ENDC} "
                      f"{bcolors.UNDERLINE}{bcolors.OKBLUE}{bcolors.UNDERLINE}PASSED{bcolors.ENDC} ")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=False,
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    degrees=int(round(degrees * self.gearRatio)),
                    speed=speed,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile)
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES: SENDING {current_command.COMMAND.hex()}...")
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self.check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()
            
        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return

    async def START_SPEED_TIME(
            self,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            time: int = 0,
            speed: int = None,
            direction: MOVEMENT = MOVEMENT.FORWARD,
            power: int = 0,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_deacc_profile: MOVEMENT = MOVEMENT.USE_DEACC_PROFILE,
            time_to_stalled: float = -1.0,
            result: Future = None,
            waitUntil: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
    
        """
        .. py:function:: async def START_SPEED_TIME
        Turn on the motor for a given time.

        The motor can be set to turn for a given time holding the provided speed while not exceeding the provided
        power setting.

        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfortime
        -time-speed-maxpower-endstate-useprofile-0x09

        Args:
            time_to_stalled ():
            use_deacc_profile ():
            use_acc_profile ():
            use_profile ():
            on_completion ():
            power ():
            direction ():
            speed ():
            time ():
            completion_cond (MOVEMENT):
            start_cond (MOVEMENT): Sets the execution mode
            result ():
            waitUntil ():
            waitUntil_timeout ():
         
        Returns:
            bool: True if no errors in cmd_send occurred, False otherwise.

        """
    
        if self.debug:
            print(f"{bcolors.WARNING}{self.name}.START_SPEED_TIME AT THE GATES...{bcolors.ENDC} "
                  f"{bcolors.OKBLUE}{bcolors.UNDERLINE}WAITING{bcolors.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME PASSED THE GATES...")

            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {bcolors.WARNING}{self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_before}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            current_command = CMD_START_MOVE_DEV_TIME(
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    time=time,
                    speed=speed,
                    direction=direction,
                    power=power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_deacc_profile=use_deacc_profile)
        
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME SENDING {current_command.COMMAND.hex()}...")
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self.check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME SENDING COMPLETE...")

            if delay_after is not None:
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.OKBLUE}START{bcolors.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{bcolors.WARNING}DELAY_AFTER / {self.name} "
                          f"{bcolors.WARNING} WAITING FOR {delay_after}... "
                          f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKBLUE}DONE{bcolors.ENDC}"
                          )

            self.port_free_condition.notify_all()
            
        # wait_until part
        if waitUntil is not None:
            fut = Future()
            await self.wait_until(waitUntil, fut)
            done, pending = await asyncio.wait((fut,), timeout=waitUntil_timeout)
        result.set_result(s)
        return
    
    @property
    @abstractmethod
    def measure_start(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                            Union[float, int], float]]:
        """
        CONVENIENCE METHOD -- This method acts like a stopwatch. It returns the current
        raw "position" of the motor. It can be used to mark the start of an experiment.
        
        :return: The current time and raw "position" of the motor. In case a synchronized motor is
            used the dictionary holds a tuple with values for all motors (virtual and 'real').
        :rtype: Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int],
        float]]
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def measure_end(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                          Union[float, int], float]]:
        """
        CONVENIENCE METHOD -- This method acts like a stopwatch. It returns the current
        raw "position" of the motor. It can be used to mark the end of a measurement.

        :return: The current time and raw "position" of the motor. In case a synchronized motor is
            used the dictionary holds a tuple with values for all motors (virtual and 'real').
        :rtype: Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int],
        float]]
        """
        raise NotImplementedError
    
    def distance_start_end(self, gearRatio=1.0) -> Tuple:
        r = tuple(map(lambda x, y: (x - y) / gearRatio, self.measure_end, self.measure_start))
        return r
    
    def avg_speed(self, gearRatio=1.0) -> Tuple:
        startend = self.distance_start_end(gearRatio)
        dt = abs(startend[len(startend) - 1])
        r = tuple(map(lambda x: (x / dt), startend))
        return r

