"""
legoBTLE.device.AMotor
======================

This module is the base abstraction for all devices that are motors.

The abstract :class:`AMotor` baseclass models common functions of a motor.

"""
import asyncio
from abc import abstractmethod
from asyncio import CancelledError, Task
from asyncio import Event
from asyncio import sleep
from collections import defaultdict
from time import monotonic
from typing import Awaitable
from typing import Callable
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
from colorama import Fore, Style

from legoBTLE.device.ADevice import ADevice
from legoBTLE.legoWP.message.downstream import CMD_GOTO_ABS_POS_DEV
from legoBTLE.legoWP.message.downstream import CMD_MODE_DATA_DIRECT
from legoBTLE.legoWP.message.downstream import CMD_SET_ACC_DEACC_PROFILE
from legoBTLE.legoWP.message.downstream import CMD_START_MOVE_DEV_DEGREES
from legoBTLE.legoWP.message.downstream import CMD_START_MOVE_DEV_TIME
from legoBTLE.legoWP.message.downstream import CMD_START_PWR_DEV
from legoBTLE.legoWP.message.downstream import CMD_START_SPEED_DEV
from legoBTLE.legoWP.types import C
from legoBTLE.legoWP.types import DIRECTIONAL_VALUE
from legoBTLE.legoWP.types import MOVEMENT
from legoBTLE.legoWP.types import SI
from legoBTLE.legoWP.types import SUB_COMMAND
from legoBTLE.legoWP.types import WRITEDIRECT_MODE
from legoBTLE.networking.prettyprint.debug import debug_info
from legoBTLE.networking.prettyprint.debug import debug_info_begin
from legoBTLE.networking.prettyprint.debug import debug_info_end
from legoBTLE.networking.prettyprint.debug import debug_info_footer
from legoBTLE.networking.prettyprint.debug import debug_info_header


class AMotor(ADevice):
    """AMotor Class
    
    Abstract base class for Motors.
    
    Methods
    -------
    :meth:`SET_ACC_PROFILE` : bool
        Set the acceleration profile for a motor.
    
    """
    
    @property
    @abstractmethod
    def time_to_stalled(self) -> float:
        """Time To Stalled: The time after which :meth:`E_MOTOR_STALLED` may be set.
        
        The time that is allowed to pass without `port_value` changes.
        After that period `asyncio.Event` `E_MOTOR_STALLED` is set.
        
        Returns
        -------
        float
            The Time To Stalled in fractions of seconds.

        """
        raise NotImplementedError
    
    @time_to_stalled.setter
    def time_to_stalled(self, tts: float):
        raise NotImplementedError
    
    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF(gearRatio=1.0)
    
    def current_angle(self, si: SI = SI.DEG) -> float:
        """Return the current angle of the motor in DEG or RAD.
        
        The current angle takes the `gear_ratio` into account.
        
        For the raw value the `port_value` should be used.
        A possible scenario looks like:
        
        .. code-block:: python
        
            import ...
            motor0 = SingleMotor(server=('127.0.0.1', 8888), port=PORT.A)
            current_angle = motor0.port_value
            print(f"Current accumulated motor angle stands at: {current_angle})
            
            Current accumulated motor angle stands at: 2963
            
            current_angle_DEG = motor0.port_value.m_port_value_DEG
            print(f"Current accumulated motor angle in DEG stands at: {current_angle_DEG}")
            
            Current accumulated motor angle in DEG stands at: 1680.2356
    
            current_angle_DEG = motor0.current_angle(si=SI.DEG)
            print(f"Current accumulated motor angle in DEG stands at: {current_angle_DEG}")
            
            Current accumulated motor angle stands at: 1680.2356
        
        Parameters
        ----------
        si : SI, default SI.DEG
            Specifies the unit of the return value.

        Returns
        -------
        float
            The current value of the motor in the specified unit (currently DEG or RAD) scaled by the gear_ratio.
            
        """
        if si == SI.DEG:
            if self.port_value is not None:
                return self.port_value.m_port_value_DEG / self.gear_ratio
        elif si == SI.RAD:
            if self.port_value is not None:
                return self.port_value.m_port_value_RAD / self.gear_ratio
    
    def last_angle(self, si: SI = SI.DEG) -> float:
        """The last recorded motor angle.
        
        Parameters
        ----------
        si : SI
            Specifies the unit of the return value.

        Returns
        -------
        float
            The last recorded angle in units si scaled by the gear_ratio.
            
        """
        if si == SI.DEG:
            if self.last_value is not None:
                return self.last_value.m_port_value_DEG / self.gear_ratio
        elif si == SI.RAD:
            if self.last_value is not None:
                return self.last_value.m_port_value_RAD / self.gear_ratio
    
    @property
    @abstractmethod
    def synced(self) -> bool:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def stall_bias(self) -> float:
        raise NotImplementedError
    
    @stall_bias.setter
    @abstractmethod
    def stall_bias(self, stall_bias: float):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def E_MOTOR_STALLED(self) -> Event:
        """Event indicating a stalling condition.
        
        Returns
        -------
        Event
            Indicates if motor is stalled. This event can be waited for.
        
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def max_steering_angle(self) -> float:
        raise NotImplementedError
    
    @max_steering_angle.setter
    @abstractmethod
    def max_steering_angle(self, max_steering_angle: float):
        raise NotImplementedError
    
    @property
    def _e_port_value_rcv(self) -> Event:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def ON_STALLED_ACTION(self) -> Callable[[], Awaitable]:
        raise NotImplementedError
    
    @ON_STALLED_ACTION.setter
    @abstractmethod
    def ON_STALLED_ACTION(self, action: Callable[[], Awaitable]):
        raise NotImplementedError
    
    @ON_STALLED_ACTION.deleter
    @abstractmethod
    def ON_STALLED_ACTION(self):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def stall_guard(self) -> Task:
        raise NotImplementedError
    
    @stall_guard.setter
    @abstractmethod
    def stall_guard(self, stall_guard: Task):
        raise NotImplementedError
    
    async def _stall_detection_init(self,
                                    cmd_id: Optional[str] = None,
                                    debug: Optional[bool] = None,
                                    ) -> Task:
        _debug = self.debug if debug is None else debug
        task: Task = asyncio.create_task(self._stall_detection(debug=True))
        debug_info_header(f"[{cmd_id}]-[MSG]", debug=_debug)
        
        debug_info(f"Task: {task} -> STALL_DETECTION READY", debug=_debug)
        debug_info(
            f"ON_STALLED_ACTION:\t{self.ON_STALLED_ACTION.__name__ if self.ON_STALLED_ACTION is not None else f'{Fore.RED}NOT SET'}",
            debug=_debug)
        self.stall_guard = task
        return self.stall_guard
    
    async def _stall_detection(self,
                               cmd_id: Optional[str] = None,
                               debug: Optional[bool] = None,
                               ) -> bool:
        _cmd_id = f"{self.__class__} {self.__name__}" if cmd_id is None else cmd_id
        _debug = self.debug if debug is None else debug
        
        try:
            while True:
                await self.E_CMD_STARTED.wait()  # await command start in cmd_feedback_notification
                await self._e_port_value_rcv.wait()  # await motor data is actually coming in
                self.E_MOTOR_STALLED.clear()
                if self.time_to_stalled is not None:  # is time after which motor is deemed stalled defined
                    
                    m0: float = self.port_value.m_port_value_DEG
                    await asyncio.sleep(self.time_to_stalled)  # wait stall time
                    
                    delta = abs(self.port_value.m_port_value_DEG - m0)
                    
                    self.avg_speed = delta / self.time_to_stalled
                    debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}]:\r\n"
                               f"DELTA_DEG:  {delta}\tDELTA_T:  {self.time_to_stalled}\tv:\'(°/s):  "
                               f"{self.avg_speed}\tv_max\'(°/s):  {self.max_avg_speed}", debug=debug)
                    
                    if delta < self.stall_bias:  # stall_bias will have a value in any case
                        debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: "
                                   f"{delta}  < {self.stall_bias}\t\t\t{C.FAIL}{C.BOLD}STALLED STALLED STALLED{C.ENDC}",
                                   debug=debug)
                        self.E_MOTOR_STALLED.set()  # motor is stalled now
                        
                        if self.ON_STALLED_ACTION is not None:  # is an action set for the case we stall
                            debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}] >>> CALLING {C.FAIL} "
                                       f"{self.ON_STALLED_ACTION}", debug=debug)
                            result = await self.ON_STALLED_ACTION()
                            debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}] >>> CALLING {C.FAIL} "
                                       f"succeeded with result {result}",
                                       debug=debug)
                            del self.ON_STALLED_ACTION  # action on stalled can only be used once, motor can't move anymore
                            self._e_port_value_rcv.clear()
                
                else:  # user doesn't want any stall detection
                    await asyncio.sleep(0.001)
        
        except CancelledError as stall_detection_shutdown:
            debug_info(f"{Style.BRIGHT}{Fore.BLUE}{12 * '*'}{Style.NORMAL} {_cmd_id}", debug=debug)
        
        return True
    
    @property
    @abstractmethod
    def wheel_diameter(self) -> float:
        """Get the diameter of the wheel(s) attached to this motor.
        
        Returns
        -------
        float
            The wheel diameter in mm.
            
        """
        raise NotImplementedError
    
    @wheel_diameter.setter
    @abstractmethod
    def wheel_diameter(self, diameter: float = 100.0):
        """Set the diameter of the wheel(s) attached to this motor.
        
        Parameters
        ----------
        diameter : float
            The wheel diameter in mm.

        Returns
        -------
        None
            Setter
            
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def gear_ratio(self) -> float:
        """Gear Ratio
        
        Returns
        -------
        float
            The gear ratio.
            
        """
        raise NotImplementedError
    
    @gear_ratio.setter
    @abstractmethod
    def gear_ratio(self, gear_ratio: float) -> None:
        """Sets the gear ratio(s) for the motor(s)
        
        Parameters
        ----------
        gear_ratio : float
            The gear ratio.
            
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def current_profile(self) -> defaultdict:
        """The profile number of the currently set acc/dec profile.

        Returns
        -------
        defaultdict
        
        """
        raise NotImplementedError
    
    @current_profile.setter
    @abstractmethod
    def current_profile(self, profile: defaultdict):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def acc_dec_profiles(self) -> defaultdict:
        """acc_dec_profiles
        
        Returns
        -------
        defaultdict

        """
        raise NotImplementedError
    
    @acc_dec_profiles.setter
    @abstractmethod
    def acc_dec_profiles(self, profile: defaultdict):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def clockwise_direction(self) -> MOVEMENT:
        """The modifier to match the real clockwise turning direction.
        
        By defining the clockwise direction of this motor, the model can be aligned with the reality.
        Thus, by defining::
        
            FORWARD_MOTOR: SingleMotor = SingleMotor(...)
            FORWARD_MOTOR.clockwise_direction_synced = MOVEMENT.COUNTERCLOCKWISE
        
        The user defined that the model's ``FORWARD_MOTOR`` motor's clockwise direction should in reality be a
        counter-clockwise movement.
         
        Returns
        -------
        MOVEMENT
           The real turning direction.
            
        """
        raise NotImplementedError
    
    @clockwise_direction.setter
    @abstractmethod
    def clockwise_direction(self, real_clockwise_direction):
        raise NotImplementedError
    
    async def SET_DEC_PROFILE(self,
                              ms_to_zero_speed: int,
                              profile_nr: int,
                              wait_cond: Union[Awaitable, Callable] = None,
                              wait_cond_timeout: float = None,
                              delay_before: float = None,
                              delay_after: float = None,
                              cmd_id: Optional[str] = '-1',
                              debug: Optional[bool] = None
                              ) -> bool:
        """
        Set the deceleration profile and profile number.
        
        The profile id then can be used in commands like :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`.
        
        Parameters
        ----------

        ms_to_zero_speed  : int
            Time allowance to let the motor come to a halt.
        profile_nr : int
            A number to save this deceleration profile under.
        wait_cond : Optional[Awaitable, Callable], optional
            A condition to wait for. The condition must be a callable that eventually results to true.
        wait_cond_timeout : float, optional
            An optional timeout after which the Condition is deemed true.
        delay_before : float, optional
            Add an optional delay before actual command execution (sending).
        delay_after : float, optional
            Add an optional delay after actual command execution (return from coroutine).
        
        Returns
        -------
        bool
            True if everything was OK, False otherwise.
            
        Raises
        ------
        TypeError, KeyError
            If None is erroneously given for `ms_to_zero_speed`, the algorithm tries to find the profile number in
            earlier defined profiles. If that fails the ``KeyError`` is raised, if something has been found but is of
            wrong type the ``TypeError`` is raised.
            
        See
        ---
        :meth:`legoBTLE.device.AMotor.SET_ACC_PROFILE`
            The counter-part of this method, i.e., controlling the acceleration.
        
        """
        if self.no_exec:
            self.no_exec = False
            return True
        
        debug = self.debug if debug is None else debug
        
        command = CMD_SET_ACC_DEACC_PROFILE(
                profile_type=SUB_COMMAND.SET_DEACC_PROFILE,
                port=self.port,
                start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                time_to_full_zero_speed=ms_to_zero_speed,
                profile_nr=profile_nr,
                )
        
        debug_info_header(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>", debug=debug)
        debug_info_begin(
                f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: AT THE GATES: {C.WARNING}WAITING",
                debug=debug)
        async with self.port_free_condition:
            
            debug_info_begin(
                    f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}WAITING",
                    debug=debug)
            
            await self.port_free.wait()
            
            debug_info_end(
                    f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}SET",
                    debug=debug)
            debug_info(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: LOCKING PORT",
                       debug=debug)
            
            self.port_free.clear()
            
            if delay_before:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying [send_cmd({command.COMMAND.hex()}) for: {delay_before}-T0]",
                        debug=debug)
                
                await sleep(delay_before)
                
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying [send_cmd({command.COMMAND.hex()}) for: {delay_before}-T0]",
                        debug=debug)
            
            if not ms_to_zero_speed >= 0:
                try:
                    command = self.acc_dec_profiles[profile_nr]['DEC']
                except (TypeError, KeyError) as ke:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    debug_info(
                            f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>: {C.WARNING}EXCEPTION: No speed setting given, tied to find already saved profile - FAILED",
                            debug=debug)
                    debug_info_footer(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>",
                                      debug=debug)
                    raise Exception(f"SET_DEC_PROFILE {profile_nr} not found... {ke.args}")
            else:
                try:
                    self.acc_dec_profiles[profile_nr]['DEC'] = command
                    self.current_profile['DEC'] = (profile_nr, command)
                except TypeError as te:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    debug_info(
                            f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>: {C.WARNING}EXCEPTION: SAVING PROFILE - FAILED",
                            debug=debug)
                    debug_info_footer(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>",
                                      debug=debug)
                    raise TypeError(f"SET_DEC_PROFILE {type(profile_nr)} wrong... {te.args}")
            
            debug_info_begin(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>:    SENDING CMD",
                             debug=debug)
            debug_info(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>:    CMD: {command.COMMAND.hex()}",
                       debug=debug)
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            s = await self._cmd_send(command)
            await self.E_CMD_STARTED.wait()
            
            debug_info_end(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>:    CMD SENT",
                           debug=debug)
            
            _t0 = monotonic()
            debug_info(f"{cmd_id} +*+ MOTOR {self.name} -- PORT {self.port[0]}>:    COMMAND END:    {C.WARNING}"
                       f"WAITED -- t0={_t0}s", debug=debug)
            
            await self.E_CMD_FINISHED.wait()
            
            _t0 = monotonic()
            if delay_after:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying [return from method] for: {delay_before}-T0",
                        debug=debug)
                
                await sleep(delay_after)
                
                debug_info_end(
                    f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying [return from method] for: dt={monotonic() - _t0}s",
                    debug=debug)
            
            try:
                if _wcd is not None:
                    _wcd.cancel()
            except (CancelledError, AttributeError, TypeError):
                pass
            self.port_free_condition.notify_all()
        debug_info_footer(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>",
                          debug=debug)
        self.no_exec = False
        return s
    
    async def SET_ACC_PROFILE(self,
                              ms_to_full_speed: int,
                              profile_nr: int,
                              wait_cond: Union[Awaitable, Callable] = None,
                              wait_cond_timeout: float = None,
                              delay_before: float = None,
                              delay_after: float = None,
                              cmd_id: Optional[str] = '-1',
                              debug: Optional[bool] = None,
                              ) -> bool:
        """Define an Acceleration Profile and assign it an id.

        This method defines an Acceleration Profile and assigns a `profile_id`.
        It saves or updates the list of Acceleration Profiles and can be used in Motor Commands like
        :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`

        Parameters
        ----------
        cmd_id :
        debug :
        ms_to_full_speed : int
            Time after which the full speed is reached (100% relative, i.e. if the top speed is limited to 40% the 100%
            equal these 40%).
        delay_before : float, optional
            Milliseconds (ms) to wait before sending this command.
        delay_after : float, optional
            Milliseconds (ms) to wait, before continuing with the program execution.
        profile_nr : int
            The Profile ID-Nr..
        wait_cond : Union[Awaitable, Callable], optional.
            Instructs to wait until ``typing.Awaitable`` or ``typing.Callable`` is True.
        wait_cond_timeout : float, optional
            Sets an additional timeout after which waiting is quit.

        Returns
        --------
        bool
            True if all is good, False otherwise.
            
        See Also
        --------
        SET_DEC_PROFILE : The counter-part of this method, i.e., controlling the acceleration.
        
        """
        if self.no_exec:
            self.no_exec = False
            return True
        
        debug = self.debug if debug is None else debug
        
        command = CMD_SET_ACC_DEACC_PROFILE(
                profile_type=SUB_COMMAND.SET_ACC_PROFILE,
                port=self.port,
                start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                time_to_full_zero_speed=ms_to_full_speed,
                profile_nr=profile_nr,
                )
        
        debug_info_header(f"COMMAND {cmd_id} +*+ <{self.name}: {self.port[0]}>", debug=debug)
        debug_info_begin(
                f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: AT THE GATES: {C.WARNING}WAITING",
                debug=debug)
        
        async with self.port_free_condition:
            
            debug_info_begin(
                    f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}WAITING",
                    debug=debug)
            
            await self.port_free.wait()
            
            debug_info_end(
                    f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}SET",
                    debug=debug)
            debug_info(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: LOCKING PORT",
                       debug=debug)
            
            self.port_free.clear()
            
            if delay_before:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>",
                        debug=debug)
                
                await sleep(delay_before)
                
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>",
                        debug=debug)
            
            if not ms_to_full_speed >= 0:
                try:
                    command = self.acc_dec_profiles[profile_nr]['ACC']
                except (TypeError, KeyError) as ke:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    
                    debug_info(
                            f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>: {C.WARNING}EXCEPTION: No speed setting given, tied to find already saved profile - FAILED",
                            debug=debug)
                    debug_info_footer(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>",
                                      debug=debug)
                    raise Exception(f"SET_ACC_PROFILE {profile_nr} not found... {ke.args}")
            else:
                try:
                    self.acc_dec_profiles[profile_nr]['ACC'] = command
                    self.current_profile['ACC'] = (profile_nr, command)
                except TypeError as te:
                    self.port_free.set()
                    self.port_free_condition.notify_all()
                    
                    debug_info(
                            f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>: {C.WARNING}EXCEPTION: SAVING PROFILE - FAILED",
                            debug=debug)
                    debug_info_footer(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>",
                                      debug=debug)
                    raise TypeError(f"Profile id [tp_id] is {profile_nr}... {te.args}")
            
            debug_info_begin(f" {cmd_id} +*+ <{self.name}: {self.port[0]}>:    SENDING CMD",
                             debug=debug)
            debug_info(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>:    CMD: {command}",
                       debug=debug)
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            s = await self._cmd_send(command)
            debug_info_end(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>:    CMD SENT",
                           debug=debug)
            
            await self.E_CMD_STARTED.wait()
            t0 = monotonic()
            debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>:    COMMAND END:    {C.WARNING}"
                       f"WAITING -- t0={t0}s", debug=debug)
            await self.E_CMD_FINISHED.wait()
            debug_info(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>:    COMMAND END:    {C.WARNING}"
                       f"WAITED: dt={monotonic() - t0}s", debug=debug)
            
            if delay_after:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying method return",
                        debug=debug)
                
                await sleep(delay_after)
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: delaying method return",
                        debug=debug)
            try:
                if _wcd is not None:
                    _wcd.cancel()
            except (CancelledError, AttributeError, TypeError):
                pass
            
            self.port_free_condition.notify_all()
        debug_info_footer(f"COMMAND {cmd_id}: <{self.name}: {self.port[0]}>",
                          debug=debug)
        return s
    
    async def START_MOVE_DISTANCE(self,
                                  distance: float,
                                  speed: Union[int, DIRECTIONAL_VALUE],
                                  abs_max_power: int = 30,
                                  use_profile: int = 0,
                                  use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
                                  use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
                                  on_completion: MOVEMENT = MOVEMENT.BREAK,
                                  on_stalled: Awaitable = None,
                                  time_to_stalled: float = None,
                                  wait_cond: Union[Awaitable, Callable] = None,
                                  wait_cond_timeout: float = None,
                                  delay_before: float = None,
                                  delay_after: float = None,
                                  cmd_id: Optional[str] = None,
                                  debug: Optional[bool] = False,
                                  ):
        """Convenience Method to drive the model a certain distance.
        
        The method uses :meth:`START_MOVE_DEGREES` and calculates with a simple rule of three the degrees to turn in
        order to reach the distance.

        Parameters
        ----------
        distance : float
            Distance to drive in mm-fractions. :func:`~np._sign(distance)` determines the direction as does ``speed``.
        speed : int
            The speed to reach the target. :func:`~np._sign(speed)` determines the direction ``distance``.
        abs_max_power : int, default=30
            Maximum power level the System can reach.
        use_profile :
            Set the ACC/DEC-Profile number
        use_acc_profile : MOVEMENT
        
            *  `MOVEMENT.USE_PROFILE` to use the acceleration profile set with use_profile.
            *  `MOVEMENT.NOT_USE_PROFILE` to not use the profile set with use_profile.
        
        use_dec_profile : MOVEMENT
            
            *  `MOVEMENT.USE_PROFILE` to use the deceleration profile set with `use_profile`.
            *  `MOVEMENT.NOT_USE_PROFILE` to not use the profile set with `use_profile`.
            
        on_completion : MOVEMENT
            Determine how the motor should behave when finished movement.
        on_stalled : Awaitable
            Determine how the motor should behave stalled condition is detected. This parameter is an ``~asyncio.Awaitable``.
        time_to_stalled : float
            Determines the elapsed time after which the motor is deemed stalled.
        wait_cond : Callable
            Wait until a Condition is met. Must be a Callable evaluating to TRUE/FALSE.
        wait_cond_timeout : float
            Determines the elapsed time after which the WaitUntil-Condition is deemed met.
        delay_before : float
            Determines elapsed ms-fractions after which the motor starts to turn.
        delay_after :
            Determines elapsed ms-fractions after which the command may return.
        
        .. note::
            As mentioned above, ``distance`` and ``speed`` influence the direction of the movement:
        
        Returns
        -------
        bool
            TRUE if all is good, FALSE otherwise.
            
        """
        degrees = np.floor((distance * 360) / (np.pi * self.wheel_diameter))
        s = await self.START_MOVE_DEGREES(degrees=degrees,
                                          speed=speed,
                                          abs_max_power=abs_max_power,
                                          on_completion=on_completion,
                                          on_stalled=on_stalled,
                                          use_profile=use_profile,
                                          use_acc_profile=use_acc_profile,
                                          use_dec_profile=use_dec_profile,
                                          time_to_stalled=time_to_stalled,
                                          wait_cond=wait_cond,
                                          wait_cond_timeout=wait_cond_timeout,
                                          delay_before=delay_before,
                                          delay_after=delay_after,
                                          cmd_id=cmd_id,
                                          debug=debug, )
        
        self.total_distance += abs(distance)
        return s
    
    async def START_POWER_UNREGULATED(self,
                                      power: Union[int, DIRECTIONAL_VALUE],
                                      start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                      on_stalled: Awaitable = None,
                                      time_to_stalled: float = None,
                                      wait_cond: Union[Awaitable, Callable] = None,
                                      wait_cond_timeout: float = None,
                                      delay_before: float = None,
                                      delay_after: float = None,
                                      cmd_id: Optional[str] = '-1',
                                      debug: Optional[bool] = None
                                      ):
        """ This command puts a certain amount of power to the Motor.
        
        The motor, or virtual motor will not start turn but is merely pre-charged. This results in a more/less forceful
        turn when the command :meth:`START_SPEED_UNREGULATED` is sent.
        
        Parameters
        ------------
        power : int
            The power to apply.
        start_cond : MOVEMENT
            Lalles
        time_to_stalled : float
            Set the timeout after which the motor, resp. this command is deemed stalled.
       
        Returns
        -------
        bool
            ``True`` if all is good, ``False`` otherwise.
        
        See Also
        --------
        `LEGO(c): START_POWER_UNREGULATED
        <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startpower-power>`_.
        
        """
        self.time_to_stalled = time_to_stalled
        self.ON_STALLED_ACTION = on_stalled
        
        power *= self.clockwise_direction  # normalize speed
        if isinstance(power, DIRECTIONAL_VALUE):
            _power = power.value * int(np.sign(power.value)) * self.clockwise_direction
        else:
            _power = power * int(np.sign(power)) * self.clockwise_direction
        
        _debug = self.debug if debug is None else debug
        command = CMD_START_PWR_DEV(
                synced=False,
                port=self.port,
                power=_power,
                start_cond=start_cond,
                completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS
                )
        
        debug_info_header(f"NAME: {self.name} / PORT: {self.port} # START_POWER_UNREGULATED", debug=_debug)
        debug_info_begin(f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # WAITING AT THE GATES",
                         debug=_debug)
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            
            debug_info_end(f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # PASSED THE GATES",
                           debug=_debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # delay_before {delay_before}s",
                        debug=_debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # delay_before {delay_before}s",
                        debug=_debug)
            
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # sending CMD", debug=_debug)
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            s = await self._cmd_send(command)
            await self.E_CMD_STARTED.wait()
            debug_info(f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # CMD: {command}",
                       debug=_debug)
            debug_info_end(
                    f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # sending CMD", debug=_debug)
            t0 = monotonic()
            debug_info(f"WAITING FOR COMMAND END: t0={t0}s", debug=_debug)
            await self.E_CMD_FINISHED.wait()
            debug_info(f"WAITED {monotonic() - t0}s FOR COMMAND TO END...", debug=_debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=_debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port} / START_POWER_UNREGULATED # delay_after {delay_after}s",
                        debug=_debug)
        
        try:
            if _wcd is not None:
                _wcd.cancel()
        except (CancelledError, AttributeError):
            pass
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port} # START_POWER_UNREGULATED",
                          debug=_debug)
        return s
    
    async def START_SPEED_UNREGULATED(
            self,
            speed: Union[int, DIRECTIONAL_VALUE],
            abs_max_power: int = 30,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_stalled: Optional[Awaitable] = None,
            time_to_stalled: Optional[float] = None,
            wait_cond: Union[Awaitable, Callable] = None,
            wait_cond_timeout: Optional[float] = None,
            delay_before: Optional[float] = None,
            delay_after: Optional[float] = None,
            cmd_id: Optional[str] = 'START_SPEED_UNREGULATED',
            debug: Optional[bool] = None,
            ):
        
        """Start the motor.
        
        The motor will run indefinitely long without applying any speed regulation.
        
        Parameters
        ----------
        debug : bool
            ``True`` if debug messages for this command are wanted, False otherwise.
        cmd_id : str, optional, default 'START_SPEED_UNREGULATED'
        on_stalled : Awaitable, optional
            The action that should be performed when stalled.
        delay_after : float
            A time period to delay the method's return.
        delay_before : float
            A time period to delay start of of command execution.
        time_to_stalled : float
            A time period after which the this motor is deemed stalled.
        start_cond : MOVEMENT
            set how the command should be executed on the hub: MOVEMENT.ONSTART_EXEC_IMMEDIATELY or MOVEMENT.ONSTART_BUFFER_IF_NEEDED
        completion_cond : MOVEMENT
        speed : int
            The speed in percent 1% - 100%.
        abs_max_power : int
            The maximum power the motor is allowed to use 1% -100%.
        use_profile : int, default 0
            The acc/dec-profile nr. See also: :meth:`SET_ACC_PROFILE` and :meth:`SET_DEC_PROFILE`.
        use_acc_profile : MOVEMENT
        use_dec_profile : MOVEMENT
        wait_cond : float
        wait_cond_timeout : float
        
        .. note::
            If the port is a virtual port, both attached motors are started.
            Motors must actively be stopped with command STOP, a reset command or a command setting the position.
            
        .. seealso::
            See `LEGO(c): START SPEED UNREGULATED <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07>`_
        for a complete command description.
        
        """
        self.time_to_stalled = time_to_stalled
        self.ON_STALLED_ACTION = on_stalled
        
        if isinstance(speed, DIRECTIONAL_VALUE):
            _speed = speed.value * self.clockwise_direction  # normalize speed
        else:
            _speed = speed * self.clockwise_direction  # normalize speed
        _debug = self.debug if debug is None else debug
        
        command = CMD_START_SPEED_DEV(
                synced=False,
                port=self.port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed=_speed,
                abs_max_power=abs_max_power,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_dec_profile=use_dec_profile)
        
        debug_info_header(f"{self.name}:{self.port}.START_SPEED_UNREGULATED()", debug=_debug)
        debug_info(f"{self.name}:{self.port}.START_SPEED_UNREGULATED(): AT THE GATES - WAITING", debug=_debug)
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            
            debug_info(f"{self.name}:{self.port}.START_SPEED_UNREGULATED(): AT THE GATES - PASSED", debug=_debug)
            if delay_before is not None:
                debug_info_begin(f"{self.name}:{self.port}.START_SPEED_UNREGULATED(): delay_before",
                                 debug=_debug)
                await sleep(delay_before)
                debug_info_end(f"{self.name}:{self.port}.START_SPEED_UNREGULATED(): delay_before",
                               debug=_debug)
            
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            s = await self._cmd_send(command)
            await self.E_CMD_STARTED.wait()
            t0 = monotonic()
            debug_info(f"WAITING FOR COMMAND END: t0={t0}s", debug=_debug)
            await self.E_CMD_FINISHED.wait()
            debug_info(f"WAITED {monotonic() - t0}s FOR COMMAND TO END...", debug=_debug)
            
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
        try:
            if _wcd is not None:
                _wcd.cancel()
        except (CancelledError, AttributeError):
            pass
        
        return s
    
    async def GOTO_ABS_POS(
            self,
            position: int,
            speed: Union[int, DIRECTIONAL_VALUE] = 30,
            abs_max_power: int = 30,
            time_to_stalled: float = None,
            on_stalled: Optional[Awaitable] = None,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            wait_cond: Union[Awaitable, Callable] = None,
            wait_cond_timeout: float = None,
            delay_before: float = None,
            delay_after: float = None,
            cmd_id: Optional[str] = 'GOTO_ABS_POS',
            debug: Optional[bool] = None
            ):
        """Turn the Motor to an absolute position.

        A complete description is available under the `LEGO(c): GOTO ABS POS <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos-speed-maxpower-endstate-useprofile-0x0d>`_
        
        Returns
        -------
        bool
            True if OK, False otherwise.

        Parameters
        ----------

        position : int
            The position to go to.
        speed : Union[int, DIRECTIONAL_VALUE], default=30
            The speed.
        abs_max_power : int, default=30
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
        wait_cond : Callable
        wait_cond_timeout : float

        """
        self.time_to_stalled = time_to_stalled
        self.ON_STALLED_ACTION = on_stalled
        
        _wcd = None
        
        if isinstance(speed, DIRECTIONAL_VALUE):
            _speed = speed.value * self.clockwise_direction
        else:
            _speed = speed * self.clockwise_direction
        
        _gearRatio = self.gear_ratio
        _debug = self.debug if debug is None else debug
        
        command = CMD_GOTO_ABS_POS_DEV(
                synced=False,
                port=self.port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                speed=_speed,
                abs_pos=position,
                gearRatio=_gearRatio,
                abs_max_power=abs_max_power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_dec_profile=use_dec_profile,
                )
        
        debug_info_header(f"COMMAND {cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>", debug=_debug)
        debug_info_begin(
                f"{cmd_id} +*+ <{self.name}--{self.port[0]}>    AT THE GATES......{C.WARNING}WAITING",
                debug=_debug)
        
        async with self.port_free_condition:
            
            debug_info_begin(
                f"{cmd_id} +*+ <{self.name} -- {self.port[0]}>    PORT_FREE.is_set()......{C.WARNING}WAITING",
                debug=_debug)
            
            await self.port_free.wait()
            
            debug_info_end(
                    f"{cmd_id} +*+ <{self.name} -- {self.port[0]}>    PORT_FREE.is_set()......{C.WARNING}SET",
                    debug=_debug)
            debug_info(f"CMD {cmd_id} +*+ <{self.name} -- {self.port[0]}>    LOCKING PORT", debug=_debug)
            
            self.port_free.clear()
            
            debug_info_end(f"{cmd_id} +*+ <{self.name} -- {self.port[0]}>    AT THE GATES......{C.WARNING}PASSED",
                           debug=_debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying [send_cmd({command.COMMAND.hex()})] for: {delay_before}-T0]",
                        debug=_debug)
                await sleep(delay_before)
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying [send_cmd({command.COMMAND.hex()})] for: {delay_before}-T0]",
                        debug=_debug)
            
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            debug_info_begin(
                f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    sending {command.COMMAND.hex()}",
                debug=_debug)
            s = await self._cmd_send(command)
            
            await self.E_CMD_STARTED.wait()
            t0 = monotonic()
            debug_info_end(
                    f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>     sending {command.COMMAND.hex()}",
                    debug=_debug)
            debug_info_begin(f"CMD {cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    waiting for "
                             f"{command.COMMAND.hex()} to finish", debug=_debug)
            
            await self.E_CMD_FINISHED.wait()
            
            debug_info_end(
                    f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    waiting for {command.COMMAND.hex()} to finish",
                    debug=_debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying return from method for {delay_after}",
                        debug=_debug)
                await sleep(delay_after)
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>     delaying return from method for {delay_after}",
                        debug=_debug)
            try:
                if _wcd is not None:
                    _wcd.cancel()
                    await _wcd
            except (CancelledError, AttributeError):
                pass
            self.port_free_condition.notify_all()
        debug_info_footer(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>", debug=_debug)
        return s
    
    async def STOP(self,
                   delay_before: float = None,
                   delay_after: float = None,
                   cmd_id: Optional[str] = None,
                   debug: Optional[bool] = None,
                   ):
        """Stop the motor and discard the currently running operation.
        
        The execution can be delayed by setting `delay_before` and `delay_after`.
        
        For a detail description of the motor command, see `LEGO(c): STOP <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#hub-attached-i-o>`_.
        
        Parameters
        ----------
        cmd_id :
        debug :
        delay_before : float, default 0.0
            Delay command execution.
        delay_after : float, default 0.0
            Delay return from method.
            
        Returns
        -------
        bool
            Result holds the boolean status of the command-sending command.
            
        """
        
        debug = self.debug if debug is None else debug
        cmd_id = self.STOP.__qualname__ if cmd_id is None else cmd_id
        debug_info_header(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>", debug=debug)
        
        _wcd = None
        
        if delay_before:
            await asyncio.sleep(delay_before)
        
        command = CMD_MODE_DATA_DIRECT(synced=self.synced,
                                       port=self.port,
                                       start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                                       completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                                       preset_mode=WRITEDIRECT_MODE.SET_MOTOR_POWER,
                                       motor_position=0,
                                       )
        
        debug_info_begin(f"    <MOTOR {self.name} -- PORT {self.port[0]}>: sending {command.COMMAND.hex()}",
                         debug=debug)
        s = await self._cmd_send(command)
        debug_info(f"        <MOTOR {self.name} -- PORT {self.port[0]}>: DELIVERED {command.COMMAND.hex()}",
                   debug=debug)
        await self.E_CMD_FINISHED.wait()
        debug_info(
            f"        <MOTOR {self.name} -- PORT {self.port[0]}>:    RECEIVED & EXECUTED {command.COMMAND.hex()}",
            debug=debug)
        debug_info_end(f"    <MOTOR {self.name} -- PORT {self.port[0]}>:    sending {command.COMMAND.hex()}",
                       debug=debug)
        
        if delay_after:
            await asyncio.sleep(delay_after)
        
        debug_info_footer(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>", debug=debug)
        
        return s
    
    async def SET_POSITION(self,
                           pos: int = 0,
                           wait_cond: Union[Awaitable, Callable] = None,
                           wait_cond_timeout: float = None,
                           delay_before: float = None,
                           delay_after: float = None,
                           cmd_id: Optional[str] = None,
                           debug: Optional[bool] = None,
                           ):
        
        _wcd = None
        debug = self.debug if debug is None else debug
        
        command = CMD_MODE_DATA_DIRECT(
                port=self.port,
                start_cond=MOVEMENT.ONSTART_EXEC_IMMEDIATELY,
                completion_cond=MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                preset_mode=WRITEDIRECT_MODE.SET_POSITION,
                motor_position=pos,
                )
        
        debug_info_header(f"THE {cmd_id} ++ <MOTOR {self.name} -- PORT {self.port[0]}>", debug=debug)
        
        debug_info(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: LOCKING PORT...", debug=debug)
        self.port_free.clear()
        debug_info(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: AT THE GATES: {C.WARNING}PASSED",
                   debug=debug)
        
        # _wait_until part
        if wait_cond:
            _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
            await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
        
        debug_info_begin(
                f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: SENDING {command.COMMAND.hex()}: {C.WARNING}WAITING",
                debug=debug)
        
        s = await self._cmd_send(command)
        
        debug_info(
                f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>: SENDING {command.COMMAND.hex()}: {C.WARNING}SENT",
                debug=debug)
        # NO WAIT FOR CMD STARTED AS WRITEDIRECT
        t0 = monotonic()
        debug_info_begin(
            f"{cmd_id} +*+ MOTOR {self.name} -- PORT {self.port[0]}.SET_POSITION(): WAITING FOR COMMAND TO END: t0={t0}s",
            debug=debug)
        await self.E_CMD_FINISHED.wait()  # Wait for CMD-Status other than `started<<<<<<<`
        debug_info_end(
            f"{cmd_id} +*+ MOTOR {self.name} -- PORT {self.port[0]}.SET_POSITION(): WAITED {monotonic() - t0}s FOR COMMAND TO END",
            debug=debug)
        
        debug_info_end(
            f"{cmd_id} +*+ MOTOR {self.name} -- PORT {self.port[0]}.SET_POSITION(): SENT, RECEIVED AND PROCESSED: {command.COMMAND.hex()}",
            debug=debug)
        if delay_after is not None:
            debug_info_begin(f"{cmd_id} +*+ MOTOR {self.name} -- PORT {self.port[0]}.SET_POSITION(): delay_after",
                             debug=debug)
            
            await sleep(delay_after)
            
            debug_info_end(f"CMD {cmd_id}MOTOR {self.name} -- PORT {self.port[0]}.SET_POSITION(): delay_after",
                           debug=debug)
        
        try:
            if _wcd is not None:
                _wcd.cancel()
        except CancelledError as ce:
            print(f"CMD: {cmd_id} + ++ ) WAIT_CONDITION.cancel() error")
        
        debug_info_footer(f"COMMAND {cmd_id}: <MOTOR {self.name} -- PORT {self.port[0]}> ++ dt = {monotonic() - t0}..",
                          debug=debug)
        
        return s
    
    async def START_MOVE_DEGREES(self,
                                 degrees: int,
                                 speed: Union[int, DIRECTIONAL_VALUE],
                                 abs_max_power: int = 30,
                                 time_to_stalled: float = None,
                                 start_cond: MOVEMENT = MOVEMENT.ONSTART_BUFFER_IF_NEEDED,
                                 completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
                                 on_completion: MOVEMENT = MOVEMENT.BREAK,
                                 use_profile: int = 0,
                                 use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
                                 use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
                                 wait_cond: Union[Awaitable, Callable] = None,
                                 wait_cond_timeout: float = None,
                                 delay_before: float = None,
                                 delay_after: float = None,
                                 cmd_id: Optional[str] = None,
                                 on_stalled: Optional[Awaitable] = None,
                                 debug: Optional[bool] = None,
                                 ):
        """Move the Motor by a number of degrees.
        
        Parameters
        ----------
        degrees : int
            The target angle to reach (default in DEG).
        speed : int
            The desired speed in % max.
        abs_max_power : int, default 30
            The absolute maximum power the motor is allowed to use to reach/keep the desired `speed`.
        on_stalled : Awaitable, optional
            Defines what the motor should do in case it reached a stalled condition
        time_to_stalled  : float, optional
            Defines the time of no motor angle changes after which the motor is deemed stalled.
        cmd_id : str, optional
            An arbitrary string as id for this actual command, so that command invocations can be identified in the
            debug output.
        debug : bool, default None
            Switch the output ON/OFF for this specific command invocation. If None, the object's setting decides.
            
        Other Parameters
        ----------------
        delay_after : float
            Time delay before executing other commands.
        delay_before : float
            Time delay, before executing THIS command.
        on_completion : {MOVEMENT.BREAK, MOVEMENT.HOLD, MOVEMENT.COAST}, MOVEMENT, optional
            Defines what the motor should do when having reached the target angle: BREAK, HOLD, COAST
        use_profile : int, default 0
            The DEC/ACC_PROFILE to use.
        use_acc_profile : {MOVEMENT.USE_ACC_PROFILE, MOVEMENT.NOT_USE_PROFILE}, MOVEMENT, default
            Use an Acceleration profile, or not.
        use_dec_profile : {MOVEMENT.USE_DEC_PROFILE, MOVEMENT.NOT_USE_PROFILE}, MOVEMENT, default
            Use an Deceleration profile, or not.
        wait_cond : Optional[Awaitable, Callable], optional
            If set any preceding command will not finish before this command evaluated to true.
        wait_cond_timeout : float, optional
            Timeout for waiting on `wait_cond`.
        start_cond : {MOVEMENT.ONSTART_EXEC_IMMEDIATELY, MOVEMENT.ONSTART_BUFFER_IF_NEEDED}, Movement, optional
            Defines the execution mode of this command (instantly: MOVEMENT.ONSTART_EXEC_IMMEDIATELY, or put in a
            one-command buffer, allowing to let the currently running command finish).
        completion_cond : {MOVEMENT.ONCOMPLETION_UPDATE_STATUS, MOVEMENT.ONCOMPLETION_NO_ACTION}, optional, default
            Defines what the motor should do after command has finished,i.e., report its status as finished
            (MOVEMENT.ONCOMPLETION_UPDATE_STATUS) or do nothing (MOVEMENT.ONCOMPLETION_NO_ACTION).
            
        Returns
        -------
        bool
            True if all is good, False otherwise.
            
        See Also
        --------
        `LEGO(c): START MOVE DEGREES <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfordegrees-degrees-speed-maxpower-endstate-useprofile-0x0b>`_
       
        """
        self.time_to_stalled = time_to_stalled
        self.ON_STALLED_ACTION = on_stalled
        
        _wcd = None
        
        if isinstance(speed, DIRECTIONAL_VALUE):
            _speed = speed.value * int(np.sign(degrees)) * self.clockwise_direction
        else:
            _speed = speed * int(np.sign(degrees)) * self.clockwise_direction
        _degrees = int(round(abs(degrees * self.gear_ratio)))  # normalize left/right
        _abs_max_power = abs(abs_max_power)
        
        debug = self.debug if debug is None else debug
        
        command = CMD_START_MOVE_DEV_DEGREES(
                synced=False,
                port=self.port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                degrees=_degrees,
                speed=_speed,
                abs_max_power=_abs_max_power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_dec_profile=use_dec_profile,
                )
        
        debug_info_header(f"COMMAND {cmd_id} +*+ <{self.name}: {self.port[0]}>", debug=debug)
        debug_info_begin(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: AT THE GATES: {C.WARNING}WAITING",
                         debug=debug)
        async with self.port_free_condition:
            
            debug_info_begin(f"{cmd_id} +*+ {self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}WAITING",
                             debug=debug)
            debug_info(f"{cmd_id} +*+ {self.name}: {self.port[0]}>: PORT FREEE STATUS: {self.port_free.is_set()}",
                       debug=debug)
            
            await self.port_free.wait()
            self.port_free.clear()
            
            debug_info_end(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: PORT_FREE.is_set(): {C.WARNING}SET",
                           debug=debug)
            debug_info(f"CMD {cmd_id} +*+ <{self.name}: {self.port[0]}>: LOCKING PORT", debug=debug)
            
            debug_info_end(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>: AT THE GATES: {C.WARNING}PASSED",
                           debug=debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying [send_cmd({command.COMMAND.hex()})] for: {delay_before}-T0]",
                        debug=debug)
                await sleep(delay_before)
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying [send_cmd({command.COMMAND.hex()})] for: {delay_before}-T0]",
                        debug=debug)
            
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            debug_info_begin(
                f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    sending {command.COMMAND.hex()}]",
                debug=debug)
            s = await self._cmd_send(command)
            await self.E_CMD_STARTED.wait()
            t0 = monotonic()
            debug_info_end(
                f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    sending {command.COMMAND.hex()}]",
                debug=debug)
            debug_info_begin(f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    waiting for "
                             f"{command.COMMAND.hex()} to finish]", debug=debug)
            
            await self.E_CMD_FINISHED.wait()
            debug_info_end(
                    f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    waiting for {command.COMMAND.hex()} to finish]",
                    debug=debug)
            
            if delay_after:
                debug_info_begin(
                    f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying return from method for {delay_after}]",
                    debug=debug)
                await sleep(delay_after)
                debug_info_end(
                        f"{cmd_id} +*+ <MOTOR {self.name} -- PORT {self.port[0]}>    delaying return from method for {delay_after}]",
                        debug=debug)
            try:
                if _wcd is not None:
                    _wcd.cancel()
            except (CancelledError, AttributeError, TypeError):
                pass
            self.port_free_condition.notify_all()
        debug_info_footer(f"{cmd_id} +*+ <{self.name}: {self.port[0]}>", debug=debug)
        return s
    
    async def START_SPEED_TIME(
            self,
            time: int,
            speed: Union[int, DIRECTIONAL_VALUE],
            power: int = 30,
            start_cond: MOVEMENT = MOVEMENT.ONSTART_BUFFER_IF_NEEDED,
            completion_cond: MOVEMENT = MOVEMENT.ONCOMPLETION_UPDATE_STATUS,
            on_completion: MOVEMENT = MOVEMENT.BREAK,
            on_stalled: Optional[Awaitable] = None,
            use_profile: int = 0,
            use_acc_profile: MOVEMENT = MOVEMENT.USE_ACC_PROFILE,
            use_dec_profile: MOVEMENT = MOVEMENT.USE_DEC_PROFILE,
            time_to_stalled: float = None,
            wait_cond: Union[Callable, Awaitable] = None,
            wait_cond_timeout: Optional[float] = None,
            delay_before: Optional[float] = None,
            delay_after: Optional[float] = None,
            cmd_id: Optional[str] = None,
            debug: Optional[bool] = None,
            ):
        """Turn on the motor for a given time.
        
        Turn on the motor for a given time after time has finished, stop
        
        The motor can be set to turn for a given time holding the provided speed while not exceeding the provided
        power setting.

        Parameters
        ----------
        time_to_stalled :
        completion_cond :
        start_cond :
        power :
        speed :
        time :
        debug :
        cmd_id :
        wait_cond_timeout :
        delay_before :
        delay_after :
        use_dec_profile :
        use_acc_profile :
        wait_cond :
        on_completion :
        use_profile :
        on_stalled :
        
        Returns
        -------
        bool
            True if no errors in _cmd_send occurred, False otherwise.

        See Also
        --------
        `LEGO(c): START SPEED FOR TIME <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeedfortime-time-speed-maxpower-endstate-useprofile-0x09>`_.
        
        """
        self.time_to_stalled = time_to_stalled
        self.ON_STALLED_ACTION = on_stalled
        
        _wcd = None
        if isinstance(speed, DIRECTIONAL_VALUE):
            _speed = speed.value * self.clockwise_direction  # normalize speed
        else:
            _speed = speed * self.clockwise_direction  # normalize speed
        _debug = self.debug if debug is None else debug
        
        command = CMD_START_MOVE_DEV_TIME(
                port=self.port,
                start_cond=start_cond,
                completion_cond=completion_cond,
                time=time,
                speed=_speed,
                power=power,
                on_completion=on_completion,
                use_profile=use_profile,
                use_acc_profile=use_acc_profile,
                use_dec_profile=use_dec_profile)
        
        async with self.port_free_condition:
            await self.port_free.wait()
            self.port_free.clear()
            
            debug_info_end(f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # PASSED THE GATES",
                           debug=_debug)
            
            if delay_before is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # delay_before {delay_before}s",
                        debug=_debug)
                await sleep(delay_before)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # delay_before {delay_before}s",
                        debug=_debug)
            
            debug_info_begin(
                    f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # sending CMD",
                    debug=_debug)
            # _wait_until part
            if wait_cond:
                _wcd = asyncio.create_task(self._on_wait_cond_do(wait_cond=wait_cond))
                await asyncio.wait({_wcd}, timeout=wait_cond_timeout)
            
            s = await self._cmd_send(command)
            
            debug_info(f"CMD:  {cmd_id} +++ [{self.name}:{self.port}]: WAITING FOR COMMAND TO START", debug=_debug)
            await self.E_CMD_STARTED.wait()
            t0 = monotonic()
            debug_info(f"CMD:  {cmd_id} +++ WAITING FOR COMMAND END: t0={t0}s", debug=_debug)
            await self.E_CMD_FINISHED.wait()
            debug_info(f"CMD:  {cmd_id} +++ WAITED {monotonic() - t0}s FOR COMMAND TO END...", debug=_debug)
            
            debug_info(
                f"CMD:  {cmd_id} +++ NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # CMD: {command}",
                debug=_debug)
            debug_info_end(
                f"CMD:  {cmd_id} +++ NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # sending CMD",
                debug=_debug)
            
            if delay_after is not None:
                debug_info_begin(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # delay_after {delay_after}s",
                        debug=_debug)
                await sleep(delay_after)
                debug_info_end(
                        f"NAME: {self.name} / PORT: {self.port[0]} / START_SPEED_TIME # delay_after {delay_after}s",
                        debug=_debug)
            
            try:
                if _wcd is not None:
                    _wcd.cancel()  # end Task
                    await _wcd  # check if really ended
            except (CancelledError, AttributeError, TypeError):
                pass
            self.port_free_condition.notify_all()
        debug_info_footer(footer=f"NAME: {self.name} / PORT: {self.port[0]} # START_SPEED_TIME",
                          debug=_debug)
        
        return s
    
    @property
    @abstractmethod
    def measure_start(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                            Union[float, int], float]]:
        """CONVENIENCE METHOD -- This method acts like a stopwatch.
        
        It returns the current raw "position" of the motor. It can be used to mark the start of an experiment.
        
        Returns
        -------
        Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int], float]]
            The current time and raw "position" of the motor. In case a synchronized motor is
            used the dictionary holds a tuple with values for all motors (virtual and 'real').
            
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def measure_end(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                          Union[float, int], float]]:
        """CONVENIENCE METHOD -- This method acts like a stopwatch.
        
        It returns the current raw "position" of the motor. It can be used to mark the end of a measurement.

        Returns
        -------
        Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int],
        float]]
            The current time and raw "position" of the motor. In case a synchronized motor is used the dictionary
            holds a tuple with values for all motors (virtual and 'real').
        
        """
        raise NotImplementedError
    
    def distance_start_end(self, gear_ratio=1.0) -> Tuple:
        r = tuple(map(lambda x, y: (x - y) / gear_ratio, self.measure_end, self.measure_start))
        return r
    
    @property
    @abstractmethod
    def avg_speed(self) -> Union[float, Tuple[float, float]]:
        raise NotImplementedError
    
    @avg_speed.setter
    @abstractmethod
    def avg_speed(self, avg_speed: Union[float, Tuple[float, float]]):
        raise NotImplementedError
    
    @property
    def max_avg_speed(self) -> Union[float, Tuple[float, float]]:
        raise NotImplementedError
    
    def avg_speed_old(self, gear_ratio=1.0) -> Tuple:
        startend = self.distance_start_end(gear_ratio)
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
