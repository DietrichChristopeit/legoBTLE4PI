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

"""This class provides the concretions of the most basic baseclass for all attached Devices: ADevice.

The abstract AMotor baseclass models common specifications of a motor.
"""


import asyncio
from abc import abstractmethod
from asyncio import Event
from asyncio import sleep
from collections import defaultdict
from time import monotonic
from typing import Awaitable
from typing import Callable
from typing import Tuple
from typing import Union

import numpy as np

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.messages.downstream import CMD_GOTO_ABS_POS_DEV
from LegoBTLE.LegoWP.messages.downstream import CMD_MODE_DATA_DIRECT
from LegoBTLE.LegoWP.messages.downstream import CMD_SET_ACC_DEACC_PROFILE
from LegoBTLE.LegoWP.messages.downstream import CMD_START_MOVE_DEV_DEGREES
from LegoBTLE.LegoWP.messages.downstream import CMD_START_MOVE_DEV_TIME
from LegoBTLE.LegoWP.messages.downstream import CMD_START_PWR_DEV
from LegoBTLE.LegoWP.messages.downstream import CMD_START_SPEED_DEV
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.LegoWP.types import SI
from LegoBTLE.LegoWP.types import SUB_COMMAND
from LegoBTLE.LegoWP.types import WRITEDIRECT_MODE
from LegoBTLE.LegoWP.types import C


class AMotor(Device):
    """Abstract base class for Motors.
    
    """
    
    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF(gearRatio=1.0)
    
    def current_angle(self, si: SI = SI.DEG) -> float:
        """Return the current angle of the motor in DEG or RAD.
        
        The current angle takes the ``gear_ratio`` into account.
        
        For the raw value the :property: port_value should be used.
        
        Examples
        --------
        
        >>> current_angle = motor0.port_value
        >>> print(f"Current accumulated motor angle stands at: {current_angle}")
        2963
        
        >>> current_angle_DEG = motor0.port_value * SI.DEG
        >>> print(f"Current accumulated motor angle in DEG stands at: {current_angle_DEG}")
        1680.2356
        
        Or
        
        >>> current_angle_DEG = motor0.current_angle(si=SI.DEG)
        >>> print(f"Current accumulated motor angle in DEG stands at: {current_angle_DEG}")
        1680.2356
        
        Keyword Args
        ----------

        si : SI
            Specifies the unit of the return value.

        Returns
        -------
        float :
            The current value of the motor in the specified unit (currently DEG or RAD) scaled by the gearRatio.
        
        """
        if si == SI.DEG:
            if self.port_value.m_port_value_DEG is not None:
                return self.port_value.m_port_value_DEG * self.gearRatio
            else:
                return -1.0
        else:
            if self.port_value.m_port_value_RAD is not None:
                return self.port_value.m_port_value_RAD * self.gearRatio
            else:
                return -1.0
    
    def last_angle(self, si: SI = SI.DEG) -> float:
        """The last recorded motor angle.
        
        Keyword Args
        ----------

        si : SI
            Specifies the unit of the return value.

        Returns
        -------
        
        float :
            The last recorded angle in units si scaled by the gearRatio.

        """
        if si == SI.DEG:
            if self.last_value.m_port_value_DEG is not None:
                return self.last_value.m_port_value_DEG * self.gearRatio
            else:
                return -1.0
        else:
            if self.last_value.m_port_value_RAD is not None:
                return self.last_value.m_port_value_RAD * self.gearRatio
            else:
                return -1.0
    
    @property
    @abstractmethod
    def E_MOTOR_STALLED(self) -> Event:
        """Event for indicating stalling condition.
        
        Returns
        ---
        Event :
            Indicates if motor Stalled. This event can be waited for.
        
        """
        raise NotImplementedError
    
    def _check_stalled_cond(self, loop, last_val, last_val_time: float = 0.0, time_to_stalled: float = None):
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
        loop.call_later(time_to_stalled / 1000, self._check_stalled_cond, loop, last_val, last_val_time,
                        time_to_stalled)
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
    def acc_dec_profiles(self) -> defaultdict:
        raise NotImplementedError
    
    @acc_dec_profiles.setter
    @abstractmethod
    def acc_dec_profiles(self, profile: defaultdict):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def forward_direction(self) -> MOVEMENT:
        raise NotImplementedError

    @forward_direction.setter
    @abstractmethod
    def forward_direction(self, real_forward_direction: MOVEMENT):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def clockwise_direction(self) -> MOVEMENT:
        raise NotImplementedError

    @clockwise_direction.setter
    @abstractmethod
    def clockwise_direction(self, real_clockwise_direction):
        raise NotImplementedError
    
    async def SET_DEC_PROFILE(self,
                              ms_to_zero_speed: int,
                              profile_nr: int,
                              waitUntilCond: Callable = None,
                              waitUntil_timeout: float = None,
                              delay_before: float = 0.0,
                              delay_after: float = 0.0
                              ) -> bool:
        """
        Set the deceleration profile and profile number.
        
        The profile id then can be used in commands like :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`.
        
        Keyword Args
        ----------

        ms_to_zero_speed  : int
            Time allowance to let the motor come to a halt.
        profile_nr : int
            A number to save the this deceleration profile under.
        waitUntilCond : Optional
            A condition to wait for. The condition must be a callable that eventually results to true.
        waitUntil_timeout : Optional
            An optional timeout after which the Condition is deemed true.
        delay_before : float
            Add an optional delay before actual command execution (sending).
        delay_after : float
            Add an optional delay after actual command execution (return from coroutine).
        
        Returns
        -------
        bool :
            True if everything was OK, False otherwise.
            
        Raises
        ---
        TypeError, KeyError
            If None is erroneously given for ms_to_zero_speed, the algorithm tries to find the profile number in
            earlier defined profiles. If that fails the KeyError is risen, if something has been found but is of
            wrong type the TypeError is risen.
        """
        
        if self.debug:
            print(
                    f"{C.WARNING}{self.name}.SET_DEC_PROFILE AT THE GATES... {C.ENDC}"
                    f"{C.UNDERLINE}{C.OKBLUE}WAITING {C.ENDC}"
                    )
        
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{C.WARNING}{self.name}.SET_DEC_PROFILE AT THE GATES... {C.OKBLUE}"
                      f"{C.OKBLUE}{C.UNDERLINE}PASSED {C.ENDC}"
                      )
            if self.debug:
                print(f"{C.WARNING}DELAY_BEFORE / {self.name} "
                      f"{C.WARNING}WAITING FOR {delay_before}... "
                      f"{C.BOLD}{C.OKBLUE}START {C.ENDC}"
                      )
            await sleep(delay_before)
            if self.debug:
                print(f"{C.WARNING}DELAY_BEFORE / {self.name} "
                      f"{C.WARNING}WAITING FOR {delay_before}... "
                      f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE {C.ENDC}"
                      )
            
            current_command = None
            if ms_to_zero_speed is None:
                try:
                    current_command = self.acc_dec_profiles[profile_nr]['DEC']
                except (TypeError, KeyError) as ke:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    raise ke(f"SET_DEC_PROFILE {profile_nr} not found... {ke.args}")
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
                    self.acc_dec_profiles[profile_nr]['DEC'] = current_command
                    self.current_profile['DEC'] = (profile_nr, current_command)
                except TypeError as te:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    raise TypeError(f"SET_DEC_PROFILE {type(profile_nr)} wrong... {te.args}")
            
            if self.debug:
                print(f"{self.name}.SET_DEC_PROFILE SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            s = await self.cmd_send(current_command)
            
            if self.debug:
                print(f"{self.name}.SET_DEC_PROFILE SENDING COMPLETE...")
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            self.port_free.set()
            self.port_free_condition.notify_all()
        
        return s
    
    async def SET_ACC_PROFILE(self,
                              ms_to_full_speed: int,
                              profile_nr: int = None,
                              waitUntilCond: Callable = None,
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
            waitUntilCond (Callable): Instructs to wait until Callable is True.
            waitUntil_timeout (float): Sets an additional timeout for waiting.

        Returns:
            None
        """
        if self.debug:
            print(
                    f"{C.WARNING}{self.name}.SET_ACC_PROFILE AT THE GATES... {C.ENDC}"
                    f"{C.UNDERLINE}{C.OKBLUE}WAITING {C.ENDC}")
        
        async with self.port_free_condition:
            await self.port_free.wait()
            
            self.port_free.clear()
            
            if self.debug:
                print(f"{C.WARNING}{self.name}.SET_ACC_PROFILE AT THE GATES... {C.ENDC}"
                      f"{C.UNDERLINE}{C.OKBLUE}{C.UNDERLINE}PASSED {C.ENDC}")
            if delay_before is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_BEFORE / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START {C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"{C.WARNING}DELAY_BEFORE / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE {C.ENDC}"
                          )
            
            current_command = None
            if ms_to_full_speed is None:
                try:
                    current_command = self.acc_dec_profiles[profile_nr]['ACC']
                except (TypeError, KeyError) as ke:
                    self.port_free_condition.notify_all()
                    self.port_free.set()
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
                    self.acc_dec_profiles[profile_nr]['ACC'] = current_command
                    self.current_profile['ACC'] = (profile_nr, current_command)
                except TypeError as te:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    raise TypeError(f"Profile id [tp_id] is {profile_nr}... {te.args}")
            
            if self.debug:
                print(f"{self.name}.SET_ACC_PROFILE SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.SET_ACC_PROFILE SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            self.port_free.set()
            self.port_free_condition.notify_all()
        return s

    async def START_MOVE_DISTANCE(self,
                                  distance: float,
                                  speed: int,
                                  abs_max_power: int = 30,
                                  use_profile: int = 0,
                                  use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
                                  use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
                                  on_completion: MOVEMENT = MOVEMENT.BREAK,
                                  on_stalled: Awaitable = None,
                                  time_to_stalled: float = -1.0,
                                  waitUntilCond: Callable = None,
                                  waitUntil_timeout: float = None,
                                  delay_before: float = None,
                                  delay_after: float = None,
                                  ):
        """
        Convenience Method to drive the model a certain distance.
        
        The method uses :func: START_MOVE_DEGREES and calculates with a simple rule of three the degrees to turn in
        order to reach the distance.

        Keyword Args
        ----------

        
        distance : float
            Distance to drive in mm-fractions. :func: ``~np.sign(distance)`` determines the direction as does `speed`.
        speed : int
            The speed to reach the target. :func: ``~np.sign(speed)`` determines the direction `distance`.
        abs_max_power : int, default=30
            Maximum power level the System can reach.
        use_profile :
            Set the ACC/DEC-Profile number
        use_acc_profile : MOVEMENT
            
                * `MOVEMENT.USE_PROFILE` to use the acceleration profile set with use_profile.
            
                * `MOVEMENT.NOT_USE_PROFILE` to not use the profile set with use_profile.
        use_dec_profile : MOVEMENT
            
                * `MOVEMENT.USE_PROFILE` to use the deceleration profile set with `use_profile`.
            
                * `MOVEMENT.NOT_USE_PROFILE` to not use the profile set with `use_profile`.
        on_completion : MOVEMENT
            Determine how the motor should behave when finished movement.
        on_stalled : Awaitable
            Determine how the motor should behave stalled condition is detected. This parameter is an ``~asyncio.Awaitable``.
        time_to_stalled : float
            Determines the elapsed time after which the motor is deemed stalled.
        waitUntilCond : Callable
            Wait until a Condition is met. Must be a Callable evaluating to TRUE/FALSE.
        waitUntil_timeout : float
            Determines the elapsed time after which the WaitUntil-Condition is deemed met.
        delay_before : float
            Determines elapsed ms-fractions after which the motor starts to turn.
        delay_after :
            Determines elapsed ms-fractions after which the command may return.
        
        Note
        ----
            
        As mentioned above, ``distance`` and ``speed`` influence the direction of the movement:
        
        .. code:: python
    
            FWD: SingleMotor = SingleMotor(name='Forward Drive', port=PORT.A, gearRatio=2.67)
            FWD.START_MOVE_DISTANCE(distance=-100, speed=73, abs_abs_max_power=90,)
        
        The resulting movement is negative (FORWARD/REARWARD: depends on the motor setup).
        And
        
        ..code:: python
        
            FWD: SingleMotor = SingleMotor(name='Forward Drive', port=PORT.A, gearRatio=2.67)
            FWD.START_MOVE_DISTANCE(distance=-100,
                                    speed=-73,
                                    abs_abs_max_power=90,
                                    )
    
        The resulting movement is positive as both `distance` and `speed` are negative.
        
        Returns
        -------
        bool
            TRUE if all is good, FALSE otherwise.
        """
        self.total_distance += abs(distance)
        degrees = np.floor((distance * 360) / (np.pi * self.wheelDiameter))
        s = await self.START_MOVE_DEGREES(degrees=degrees, speed=speed, abs_max_power=abs_max_power,
                                          on_completion=on_completion, on_stalled=on_stalled, use_profile=use_profile,
                                          use_acc_profile=use_acc_profile, use_dec_profile=use_dec_profile,
                                          time_to_stalled=time_to_stalled, waitUntilCond=waitUntilCond,
                                          waitUntil_timeout=waitUntil_timeout, delay_before=delay_before,
                                          delay_after=delay_after)
        self.total_distance += abs(distance)
        return s
    
    async def START_POWER_UNREGULATED(self,
                                      power: int,
                                      start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                      on_stalled: Awaitable = None,
                                      time_to_stalled: float = -1.0,
                                      waitUntilCond: Callable = None,
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
        
        Keyword Args
        ---
        
        power : int
        start_cond : MOVEMENT
        time_to_stalled : float
            Set the timeout after which the motor, resp. this command is deemed stalled.

        
        Returns
        ---
        bool :
        
        """
        power *= self.forward_direction  # normalize speed
        
        if self.debug:
            print(
                    f"{C.WARNING}{self.name}.START_POWER_UNREGULATED AT THE GATES...{C.ENDC} "
                    f"{C.OKBLUE}{C.UNDERLINE}WAITING {C.ENDC} ")
        
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            
            if self.debug:
                print(f"{C.WARNING}{self.name}.START_POWER_UNREGULATED AT THE GATES...{C.ENDC} "
                      f"{C.UNDERLINE}{C.OKBLUE}{C.UNDERLINE}PASSED{C.ENDC} ")
            
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            current_command = CMD_START_PWR_DEV(
                    synced=False,
                    port=self.port,
                    power=power,
                    start_cond=start_cond,
                    completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS
                    )
            
            if self.debug:
                print(f"{self.name}.START_POWER_UNREGULATED SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_POWER_UNREGULATED SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
                self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()   # no manual port_free.set() here as respective
                                                    # command executed notification sets it at the right time
        return s
    
    async def START_SPEED_UNREGULATED(
            self,
            speed: int,
            abs_max_power: int = 30,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_stalled: Awaitable = None,
            time_to_stalled: float = -1.0,
            waitUntilCond: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """Start the motor.
        
        .. note::
            If the port is a virtual port, both attached motors are started.
            Motors must actively be stopped with command STOP, a reset command or a command setting the position.
        
        .. seealso::
            https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07

        Keyword Args
        
        on_stalled : 
        delay_after : float 
        delay_before : float 
        time_to_stalled : float
        start_cond :
        completion_cond :
        speed : int
            The speed in percent.
        abs_max_power :
        use_profile :
        use_acc_profile : MOVEMENT
        use_dec_profile : MOVEMENT
        waitUntilCond : float
        waitUntil_timeout : float
      
        """
        speed *= self.forward_direction  # normalize speed

        if self.debug:
            print(f"{C.WARNING}{self.name}.START_SPEED AT THE GATES...{C.ENDC} "
                  f"{C.OKBLUE}{C.UNDERLINE}WAITING{C.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{C.WARNING}{self.name}.START_SPEED AT THE GATES...{C.ENDC} "
                      f"{C.OKBLUE}{C.UNDERLINE}PASSED{C.ENDC} ")
            
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
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
                    use_dec_profile=use_dec_profile)

            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.START_SPEED SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
                self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()
        return s
    
    async def GOTO_ABS_POS(
            self,
            position: int,
            speed: int = 30,
            abs_max_power: int = 30,
            time_to_stalled: float = -1.0,
            on_stalled: Awaitable = None,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            waitUntilCond: Callable = None,
            waitUntil_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            ):
        """Turn the Motor to an absolute position.

        .. seealso::
            https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos-speed-maxpower-endstate-useprofile-0x0d

        Returns
        ---
        bool
            True if OK, False otherwise.

        Keyword Args
        ----------

        
        position : int
            The position to go to.
        speed : int, default=30
            The speed.
        abs_max_power : int,default=30
            Maximum power level the motor is allowed to apply.
        time_to_stalled : float
            Time period (ms-fractions) after which the stagnant motor is deemed stalled
        on_stalled : Callable
            Set a callback in case motor is stalled, e.g. :func: port_value_set(port_value)
        on_completion : MOVEMENT
            Defines how the motor should behave after coming to a standstill (break, hold, coast).
        start_cond : MOVEMENT
            Defines how the command should be executed (immediately, buffer if necessary, etc.)
        completion_cond : MOVEMENT
            Defines how the command should end (report status etc.)
        use_profile :
        use_acc_profile :
        use_dec_profile :
        waitUntilCond : Callable
        waitUntil_timeout : float

        """
        
        speed *= self.forward_direction  # normalize speed
        position *= self.clockwise_direction  # normalize lef/right
        
        loop = asyncio.get_running_loop()
        if self.debug:
            print(f"{C.WARNING}{self.name}.GOTO_ABS_POS AT THE GATES...{C.ENDC} "
                  f"{C.UNDERLINE}{C.OKBLUE}WAITING{C.ENDC} ")
        
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            
            if self.debug:
                print(f"{C.WARNING}{self.name}.GOTO_ABS_POS AT THE GATES...{C.ENDC} "
                      f"{C.UNDERLINE}{C.UNDERLINE}{C.OKBLUE}PASSED {C.ENDC} ")
            
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING}WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            current_command = CMD_GOTO_ABS_POS_DEV(
                    synced=False,
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    speed=speed,
                    abs_pos=position,
                    gearRatio=self.gearRatio,
                    abs_max_power=abs_max_power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile)
            if self.debug:
                print(f"{self.name}.GOTO_ABS_POS SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done= await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled > 0.0:
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self.cmd_send(current_command)
            if self.debug:
                print(f"{self.name}.GOTO_ABS_POS SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING}WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
                self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()
            
        return s
    
    async def STOP(self,
                   use_profile: int = None,
                   waitUntilCond: Callable = None,
                   waitUntil_timeout: float = None,
                   delay_before: float = None,
                   delay_after: float = None,
                   ):
        """Stop the motor immediately and cancel the currently running operation.
        
        Keyword Args:
            use_profile (int): Use this profile number for stopping.
           

        Returns:
            Nothing (None): result holds the status of the command-sending command.

        """
        if use_profile is None:
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            s = await self.START_SPEED_UNREGULATED(speed=0,
                                                   use_profile=self.current_profile['ACC'][0],
                                                   waitUntilCond=waitUntilCond,
                                                   waitUntil_timeout=waitUntil_timeout,
                                                   delay_before=delay_before,
                                                   delay_after=delay_after,
                                                   )
        else:
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            s = await self.START_SPEED_UNREGULATED(speed=0,
                                                   use_profile=use_profile,
                                                   waitUntilCond=waitUntilCond,
                                                   waitUntil_timeout=waitUntil_timeout,
                                                   delay_before=delay_before,
                                                   delay_after=delay_after,
                                                   )

        return s
    
    async def SET_POSITION(self,
                           pos: int = 0,
                           waitUntilCond: Callable = None,
                           waitUntil_timeout: float = None,
                           delay_before: float = None,
                           delay_after: float = None,
                           ):
        
        if self.debug:
            print(f"{C.WARNING}{self.name}.SET_POSITION AT THE GATES...{C.ENDC} "
                  f"{C.OKBLUE}{C.UNDERLINE}WAITING{C.ENDC} ")
        
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{C.WARNING}{self.name}.SET_POSITION AT THE GATES...{C.ENDC} "
                      f"{C.UNDERLINE}{C.OKBLUE}{C.UNDERLINE}PASSED{C.ENDC} ")
    
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
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
                
            # _wait_until part
            if waitUntilCond is not None:
                if self.debug:
                    print(f"{self.name}.SET_POSITION waiting for WaitCondition {waitUntilCond} to become True {command.COMMAND.hex()}...")
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
    
            s = await self.cmd_send(command)
            if self.debug:
                print(f"{self.name}.SET_POSITION SENDING COMPLETE...")
    
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            self.port_free_condition.notify_all()
        return s
    
    async def START_MOVE_DEGREES(self,
                                 degrees: int,
                                 speed: int,
                                 abs_max_power: int = 30,
                                 on_completion: MOVEMENT = MOVEMENT.BREAK,
                                 on_stalled: Awaitable = None,
                                 start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                 completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                                 use_profile: int = 0,
                                 use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
                                 use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
                                 time_to_stalled: float = -1.0,
                                 waitUntilCond: Callable = None,
                                 waitUntil_timeout: float = None,
                                 delay_before: float = None,
                                 delay_after: float = None,
                                 ):
        """

        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfordegrees
        -degrees-speed-maxpower-endstate-useprofile-0x0b

        Parameters
        ---
    
        delay_after : float
        delay_before : float
        on_stalled : Awaitable
        time_to_stalled  : float
        start_cond : MOVEMENT
        completion_cond : MOVEMENT
        degrees : int
        speed : int
        abs_max_power : int
        on_completion : MOVEMENT
        use_profile : int
        use_acc_profile : MOVEMENT
        use_dec_profile : MOVEMENT
        waitUntilCond : Callable
            If set any preceding command will not finish before this command
        waitUntil_timeout : float

        Returns
        ---
        
        bool
            True if no errors in cmd_send occurred, False otherwise.
        """
        speed *= self.forward_direction  # normalize speed
        # degrees *= self.clockwise_direction  # normalize lef/right
        
        if self.debug:
            print(
                    f"{C.WARNING}{self.name}.START_MOVE_DEGREES{C.ENDC} "
                    f"{C.WARNING} AT THE GATES...{C.ENDC} "
                    f"{C.UNDERLINE}{C.OKBLUE}WAITING{C.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES AT THE GATES...{C.ENDC} "
                      f"{C.UNDERLINE}{C.OKBLUE}{C.UNDERLINE}PASSED{C.ENDC} ")
            
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            current_command = CMD_START_MOVE_DEV_DEGREES(
                    synced=False,
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    degrees=int(round(degrees * self.gearRatio)),
                    speed=speed,
                    abs_max_power=abs(abs_max_power),
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile)
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES: SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self.cmd_send(current_command)
            
            if self.debug:
                print(f"{self.name}.START_MOVE_DEGREES SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
                self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()
        return s
    
    async def START_SPEED_TIME(
            self,
            time: int,
            speed: int,
            power: int = 30,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            on_stalled: Awaitable = None,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = -1.0,
            waitUntilCond: Callable = None,
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
            use_dec_profile ():
            use_acc_profile ():
            use_profile ():
            on_completion ():
            power ():
            speed ():
            time ():
            completion_cond (MOVEMENT):
            start_cond (MOVEMENT): Sets the execution mode
            waitUntilCond ():
            waitUntil_timeout ():
         
        Returns:
            bool: True if no errors in cmd_send occurred, False otherwise.

        """
        speed *= self.forward_direction  # normalize speed
        power *= self.clockwise_direction  # normalize lef/right
        
        if self.debug:
            print(f"{C.WARNING}{self.name}.START_SPEED_TIME AT THE GATES...{C.ENDC} "
                  f"{C.OKBLUE}{C.UNDERLINE}WAITING{C.ENDC} ")
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME PASSED THE GATES...")
            
            if delay_before is not None:
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_before)
                if self.debug:
                    print(f"DELAY_BEFORE / {C.WARNING}{self.name} "
                          f"{C.WARNING} WAITING FOR {delay_before}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            
            current_command = CMD_START_MOVE_DEV_TIME(
                    port=self.port,
                    start_cond=start_cond,
                    completion_cond=completion_cond,
                    time=time,
                    speed=speed,
                    power=power,
                    on_completion=on_completion,
                    use_profile=use_profile,
                    use_acc_profile=use_acc_profile,
                    use_dec_profile=use_dec_profile)
            
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME SENDING {current_command.COMMAND.hex()}...")
            # _wait_until part
            if waitUntilCond is not None:
                fut = asyncio.get_running_loop().create_future()
                await self._wait_until(waitUntilCond, fut)
                done = await asyncio.wait_for(fut, timeout=waitUntil_timeout)
            # start stall detection
            self.E_MOTOR_STALLED.clear()
            if time_to_stalled >= 0.0:
                loop = asyncio.get_running_loop()
                stalled = loop.call_soon(self._check_stalled_cond, loop, self.port_value, None, time_to_stalled)
            stalled_cb = None
            if on_stalled:
                stalled_cb = loop.create_task(on_stalled)
            s = await self.cmd_send(current_command)
            
            if self.debug:
                print(f"{self.name}.START_SPEED_TIME SENDING COMPLETE...")
            
            if delay_after is not None:
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.OKBLUE}START{C.ENDC}"
                          )
                await sleep(delay_after)
                if self.debug:
                    print(f"{C.WARNING}DELAY_AFTER / {self.name} "
                          f"{C.WARNING} WAITING FOR {delay_after}... "
                          f"{C.BOLD}{C.UNDERLINE}{C.OKBLUE}DONE{C.ENDC}"
                          )
            if on_stalled:
                try:
                    await asyncio.wait_for(fut=stalled_cb, timeout=0.0001)
                except TimeoutError:
                    stalled_cb.cancel()
                    pass
                self.E_MOTOR_STALLED.clear()
            self.port_free_condition.notify_all()
        return s
    
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
    
    @property
    @abstractmethod
    def total_distance(self) -> float:
        raise NotImplementedError
    
    @total_distance.setter
    @abstractmethod
    def total_distance(self, total_distance: float):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def distance(self) -> float:
        """Returns the total distance travelled in mm since the last reset.
        """
        raise NotImplementedError
    
    @distance.setter
    @abstractmethod
    def distance(self, distance: float):
        raise NotImplementedError
