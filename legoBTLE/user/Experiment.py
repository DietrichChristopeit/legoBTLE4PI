"""
legoBTLE.user.Experiment
~~~~~~~~~~~~~~~~~~~~~~~~

Organizes the connection establishment and setup of the all devices attached to the hub brick.

"""
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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
from __future__ import annotations

import asyncio
import itertools
from asyncio import AbstractEventLoop
from asyncio import Condition
from asyncio import Future
from asyncio import InvalidStateError
from asyncio import PriorityQueue
from collections import defaultdict
from collections import deque
from collections import namedtuple
from typing import Any
from typing import Awaitable
from typing import Coroutine
from typing import List
from typing import Tuple

from legoBTLE.device.ADevice import ADevice
from legoBTLE.device.Hub import Hub
from legoBTLE.device.SynchronizedMotor import SynchronizedMotor
from legoBTLE.legoWP.types import C
from legoBTLE.networking.prettyprint.debug import debug_info
from legoBTLE.networking.prettyprint.debug import debug_info_begin
from legoBTLE.networking.prettyprint.debug import debug_info_end
from legoBTLE.networking.prettyprint.debug import debug_info_footer
from legoBTLE.networking.prettyprint.debug import debug_info_header


class Experiment:
    """ This class models an Experiment that can be performed with the Lego devices (Motors etc.). It is suggested to
    use this class to create and run_each sequences of commands concurrently.
    However, the class is mainly a wrapper with some convenience functions. Nothing stands against using
    the 'lower level' functions.
    
    :param str name: A descriptive name.
    :param measure_time: If set, the execution time to process the Action List will be measured.
    :param debug: If set, function call info is printed.

    """
    Action = namedtuple('Action', 'cmd args kwargs only_after forever_run',
                        defaults=[None, [], defaultdict, True, False])
    
    def __init__(self, name: str, loop: AbstractEventLoop, measure_time: bool = False, debug: bool = False):
        """
        
        
        """
        self._con_device_tasks: defaultdict = defaultdict(defaultdict)
        self._name: str = name
        self._loop: AbstractEventLoop = loop
        self._tasks_runnable: List[Tuple[defaultdict[defaultdict], bool]] = []
        self._wait: Condition = Condition()
        self._measure_time: bool = measure_time
        self._runtime: float = -1.0
        self._experiment_results: Future = Future()
        self._savedResults: List[Tuple[float, defaultdict, float]] = [(-1.0, defaultdict(), -1.0)]
        self._debug = debug
        # for connecting devices to server
        self._setupQueue: PriorityQueue = PriorityQueue()
        self._devices: List[ADevice] = []
        return
    
    @property
    def name(self) -> str:
        if self._debug:
            print(f"self.name = {self._name}")
        return self._name
    
    @property
    def devices(self) -> List[ADevice]:
        """Get devices List
        
        The devices used in this experiment.
        
        Returns
        -------
        
        List[device]
            A list of devices.
        
        """
        return self._devices
    
    @devices.setter
    def devices(self, devices: List[ADevice]):
        """Set devices List
        
        The devices used in this experiment.
        
        Returns
        -------
        
        None
            Nothing, setter
            
        """
        self._devices = devices
        return
    
    def _count_iter_items(self, iterable):
        """
        Consume an iterable not reading it into memory; return the number of items.
        """
        
        counter = itertools.count()
        deque(zip(iterable, counter), maxlen=0)  # (consume at C speed)
        return next(counter) - 1
    
    async def setupConnectivity(self, devices: List[ADevice]) -> defaultdict[defaultdict]:
        r"""Connect the devices List to the Server.
        
        This method organizes the complete connection procedure until all devices attached to the model are connected
        with the Server and are able to receive notifications.
        
        Parameters
        ----------
        devices : List[device]
            A list of device objects, e.g., [Hub, Steering,...]
        """
        results: list = []
        tasks: list = []
        
        # CONNECT DEVICES
        debug_info_header("LIST OF DEVICES", debug=self._debug)
        for d in devices:
            debug_info(f"NAME: {d.name} / PORT: {d.port[0]} / TYPE: {d.__class__}", debug=self._debug)
        debug_info_footer(footer=f"LIST OF DEVICES", debug=self._debug)

        debug_info_header("SERVER CONNECTION SETUP", debug=self._debug)
        connection_results = await self._connect_devs_by(devices, 'EXT_SRV_CONNECT_REQ')
        await asyncio.sleep(1.0)
        debug_info_footer(footer=f"SERVER CONNECTION SETUP", debug=self._debug)
        
        notification_request_tasks = []
        # for hub setup
        hubs = filter(lambda x: isinstance(x, Hub), devices)
        # for setup virtual Ports
        virtualMotors = filter(lambda x: isinstance(x, SynchronizedMotor), devices)
        vms = []

        debug_info_header("VIRTUAL PORT SETUP", debug=self._debug)
        for v in virtualMotors:
            if isinstance(v, SynchronizedMotor):
                debug_info_begin(f"VIRTUAL PORT SETUP REQ: {v.name}", debug=self._debug)
                vms.append(await v.VIRTUAL_PORT_SETUP(connect=True))
                debug_info_end(f"VIRTUAL PORT SETUP REQ: {v.name}", debug=self._debug)
        debug_info(f"SETUP VIRTUAL: {*vms,}", debug=self._debug)
        debug_info_footer(footer=f"VIRTUAL PORT SETUP", debug=self._debug)

        debug_info_header("PORT NOTIFICATION SETUP for all general devices", debug=self._debug)
        for d in devices:
            if not isinstance(d, Hub):
                debug_info_begin(f"PORT NOTIFICATION REQ: {d.name}", debug=self._debug)
                notification_request_tasks.append(asyncio.create_task(d.REQ_PORT_NOTIFICATION()))
                debug_info_end(f"PORT NOTIFICATION REQ: {d.name}", debug=self._debug)
        await asyncio.sleep(1)
        debug_info_footer(footer=f"PORT NOTIFICATIONS SETUP for all general devices", debug=self._debug)

        debug_info_header("GENERAL NOTIFICATION SETUP for Hub devices", debug=self._debug)
        for h in hubs:
            if isinstance(h, Hub):
                debug_info_begin(f"GENERAL NOTIFICATION REQ: {h.name}", debug=self._debug)
                results.append(await h.REQ_PORT_NOTIFICATION(delay_after=5))
                debug_info_end(f"GENERAL NOTIFICATION REQ: {h.name}", debug=self._debug)
        await asyncio.sleep(1)
        debug_info_footer(footer=f"GENERAL NOTIFICATION SETUP for Hub devices", debug=self._debug)
        
        return self._con_device_tasks
    
    async def _connect_devs_by(self, devices: [ADevice], con_method):
        
        connection_attempts: [Coroutine] = []
        
        for d in devices:
            debug_info_begin(f"SERVER CONNECTION ATTEMPT: {d.name}", debug=self._debug)
            connection_attempts.append(getattr(d, con_method)())
            debug_info_end(f"SERVER CONNECTION ATTEMPT: {d.name}", debug=self._debug)
        
        result = await asyncio.gather(*connection_attempts, return_exceptions=True)
        
        for r in result:
            debug_info(f"RESULT CON ATTEMPT: {r}", debug=self._debug)
        
        return result
    
    @property
    def savedResults(self) -> List[Tuple[float, defaultdict, float]]:
        if self._debug:
            print(f"self.savedResults = {self._savedResults}")
        return self._savedResults
    
    @savedResults.setter
    def savedResults(self, results: [float, defaultdict, float]):
        if self._debug:
            print(f"savedResults({results}) = {self._savedResults}")
        self._savedResults.append(results)
        return
    
    @property
    def active_actionList(self) -> [defaultdict]:
        """The active Action List on which all functions run_each when no Action List as argument is given.

        :returns: The active Action List on which runExperiment is executed when no arguments are given.
        :rtype: list[Action]
        """
        if self._debug:
            print(f"self.active_actionList = {self._tasks_runnable}")
        return self._tasks_runnable
    
    @property
    def runTime(self) -> float:
        """Returns the time needed to execute the active Action List

        :return:
        """
        return self._runtime
    
    async def run_each(self, tasklist) -> defaultdict:
        """
         .. py:method::
        
        Returns:
            The results of the Experiment.

        """
        results: defaultdict = defaultdict(list)
        tasks_running: defaultdict = defaultdict(list)
        for t in tasklist:
            for c in tasklist[t]:
                tasks_running['task'] += [asyncio.create_task(c['cmd'])]
        return results
    
    async def runTask(self, task: Awaitable) -> Any:
        r"""Run a single task.
        
        Parameters
        ----------
        task : Awaitable
            The single task.
        """
        running_cmd = asyncio.create_task(task)
        
        await running_cmd
        ret = running_cmd.result()
        return ret
    
    #  def _setupNotifyConnect(self, devices: List[ADevice]) -> Experiment:
    #      """This is a generator that produces the commands to connect devices to the Server.
#
    #      Parameters
    #      ----------
    #      devices : list[device]
    #          The list of devices which should be connected to the server.
#
    #      Returns
    #      ------
    #      self : Experiment
    #          The instance's list of runnable prepareTasks contains defaultdict's that resemble the Tasks for each device to
    #          connect to the server and receive notifications.
    #      """
    #      debug_info_header(f"[{self._name}]-[MSG]:{C.ENDC}ASSEMBLING CONNECTION"
    #                        f" and NOTIFICATION Tasks...", debug=self._debug)
    #
    #      self._tasks_runnable += [
    #              {'cmd': d.EXT_SRV_CONNECT_REQ,
    #               'kwargs': {'waitUntil': (lambda: True) if d.port == devices[-1].port else None},
    #               } for d in devices]
    #
    #      self._tasks_runnable += [
    #              {'cmd': d.GENERAL_NOTIFICATION_REQUEST if isinstance(d, Hub) else d.REQ_PORT_NOTIFICATION,
    #               'kwargs': {'waitUntil': (lambda: True) if isinstance(d, Hub) else None},
    #               } for d in devices]
    #      self._tasks_runnable = self._tasks_runnable[:len(self._tasks_runnable)]
    #      return self
    
    def _getState(self) -> None:
        """
        This method prints an overview of the state of the experiment. It lists all prepareTasks according to their
        (done, pending) state with results.

        :returns: Just prints put the list.
        :rtype: None
        
        """
        pendingTasks: [] = []
        for r in self._experiment_results.result():
            for ex in self._experiment_results.result()[r][0][0]:  # done prepareTasks
                state = f"{ex.exception().args}" if ex.exception() is not None \
                    else f"HAS FINISHED WITH RESULT: {ex.result()}"
                print(f"TASK-LIST DONE {r}: Task {ex} {state}")
            for ex in self._experiment_results.result()[r][0][1]:  # pending prepareTasks
                try:
                    print(f"TASK-LIST PENDING {r}: Task {ex} {ex.exception().__str__()}")
                except InvalidStateError:
                    pendingTasks.append(ex)
                    print(f"TASK-LIST PENDING {r}: Task {ex} is WAITING FOR SOMETHING...")
                except Exception as ce:
                    raise SystemError(f"NO CONNECTION TO SERVER... GIVING UP...{ce.args}")
        return
    
    def _getDoneTasks(self):
        """
        The method returns a list of results of the done prepareTasks.

        :returns: The done task results
        :rtype: list
        """
        res: list = []
        for r in self._experiment_results.result():
            for ex in self._experiment_results.result()[r][0][0]:  # done prepareTasks
                res.append(ex)
        if self._debug:
            print(f"self._getDoneTasks -> {res}")
        return res
