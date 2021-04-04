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
from time import monotonic
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.Exceptions import LegoBTLENoHubToConnectError
from LegoBTLE.LegoWP.types import C


class Experiment:
    """ This class models an Experiment that can be performed with the Lego devices (Motors etc.). It is suggested to
    use this class to create and run sequences of commands concurrently.
    However, the class is mainly a wrapper with some convenience functions. Nothing stands against using
    the 'lower level' functions.
    
    :param str name: A descriptive name.
    :param measure_time: If set, the execution time to process the Action List will be measured.
    :param debug: If set, function call info is printed.

    """
    Action = namedtuple('Action', 'cmd args kwargs only_after forever_run',
                        defaults=[None, [], defaultdict, True, False])
    
    def __init__(self, name: str, loop: AbstractEventLoop, measure_time: bool = False, debug: bool = True):
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
        self._devices: List[Device] = []
        return
    
    @property
    def name(self) -> str:
        if self._debug:
            print(f"self.name = {self._name}")
        return self._name
    
    @property
    def devices(self) -> List[Device]:
        """Get Devices List
        
        The devices used in this experiment.
        
        Returns
        -------
        
        List[Device]
            A list of devices.
        
        """
        return self._devices
    
    @devices.setter
    def devices(self, devices: List[Device]):
        """Set Devices List
        
        The devices used in this experiment.
        
        Returns
        -------
        
        """
        self._devices = devices

    def _count_iter_items(self, iterable):
        """
        Consume an iterable not reading it into memory; return the number of items.
        """
        
        counter = itertools.count()
        deque(zip(iterable, counter), maxlen=0)  # (consume at C speed)
        return next(counter)-1
        
    async def setupConnectivity(self, devices: List[Device]) -> defaultdict[defaultdict]:
        """Connect the Devices List to the Server.

        """
        # CONNECT DEVICES
        print(f"{devices}")
        results: list = []
        tasks: list = []
        for d in devices:
            temp = self._loop.create_task(d.EXT_SRV_CONNECT())
            tasks.append(temp)
            self._con_device_tasks[(d.id, d.name)][d.EXT_SRV_CONNECT] = temp
        results.append(await asyncio.gather(*tasks, return_exceptions=True))
        if self._debug:
            print(f"*******************{C.BOLD}{C.UNDERLINE}{C.OKBLUE}[{__class__}.EXT_SRV_CONNECT]-[RESULTS]{C.ENDC}*****************************\r\n")
            for r in results:
                print(f"-[RESULTS]: {r}\r\n")
            print(
                f"*******************{C.BOLD}{C.UNDERLINE}{C.OKBLUE}[{__class__}.EXT_SRV_CONNECT]-[RESULTS] END{C.ENDC}*************************\r\n")
                
        # turn on  notifications for hub first
        hubs = filter(lambda x: isinstance(x, Hub), devices)
        hubsT = []
        for h in hubs:
            print(f"FOUND HUB: {h.name}")
            if isinstance(h, Hub):
                hubsT.append(await asyncio.wait_for(asyncio.create_task(h.REQ_PORT_NOTIFICATION(delay_after=5)), timeout=20))
        await asyncio.sleep(6)
        virtualMotors = filter(lambda x: isinstance(x, SynchronizedMotor), devices)
        vms = []
        for v in virtualMotors:
            print(f"FOUND virtual Motor: {v.name}")
            if isinstance(v, SynchronizedMotor):
                vms.append(await asyncio.wait_for(asyncio.create_task(v.VIRTUAL_PORT_SETUP(connect=True)), timeout=20))
                vms.append(await asyncio.wait_for(asyncio.create_task(v.REQ_PORT_NOTIFICATION()), timeout=20))
        
        tasks.clear()
        for d in devices:
            if isinstance(d, SynchronizedMotor):
                pass
            elif isinstance(d, Hub):
                pass
            else:
                
                temp = self._loop.create_task(d.REQ_PORT_NOTIFICATION(delay_before=1.0, delay_after=1.0))
                tasks.append(temp)
                self._con_device_tasks[(d.id, d.name)][d.REQ_PORT_NOTIFICATION] = temp
            results.append(await asyncio.gather(*tasks, return_exceptions=True))
            for result_or_exc in results:
                if isinstance(result_or_exc, Exception):
                    print(f"*******************[{C.BOLD}{C.UNDERLINE}{C.FAIL}[{__class__}.REQ_PORT_NOTIFICATION]--[ERROR]: {result_or_exc}*****************************\r\n")
        if self._debug:
            print(f"*******************{C.BOLD}{C.UNDERLINE}{C.OKBLUE}[{__class__}.REQ_PORT_NOTIFICATION]-[RESULTS]{C.ENDC}*****************************\r\n")
            for r in results:
                print(f"-[RESULTS]: {r}\r\n")
            print(f"*******************{C.BOLD}{C.UNDERLINE}{C.OKBLUE}[{__class__}.REQ_PORT_NOTIFICATION]-[RESULTS] END{C.ENDC}*************************\r\n")
        return self._con_device_tasks
    
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
        """The active Action List on which all functions run when no Action List as argument is given.

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
    
    async def run(self, tasklist) -> defaultdict:
        """
         .. py:method::
        
        Returns:
            The results of the Experiment.

        """
        print(f"{C.OKBLUE}{C.UNDERLINE}IN EXPERIMENT.run...{C.ENDC}\r\n")
        print(f"{tasklist}")
        results: defaultdict = defaultdict(list)
        tasks_running: defaultdict = defaultdict(list)
        for t in tasklist:
            for c in tasklist[t]:
                tasks_running['task'] += [asyncio.create_task(c['cmd'](*c.get('args', []), **c.get('kwargs', {})))]
                print(f"{c['cmd']}")
        print(f"{tasks_running}")
    
        return results
    
    def _setupNotifyConnect(self, devices: List[Device]) -> Experiment:
        """This is a generator that yields the commands to connect Devices to the Server.

        Parameters
        ----------
        devices : list[Device]
            The list of devices which should be connected to the server.

        Returns
        ------
        self : Experiment
            The instance's list of runnable prepareTasks contains defaultdict's that resemble the Tasks for each device to
            connect to the server and receive notifications.
        """
        if self._debug:
            print(f"{C.BOLD}{C.OKBLUE}[{self._name}]-[MSG]:{C.ENDC}ASSEMBLING CONNECTION"
                  f" and NOTIFICATION Tasks...")
        
        self._tasks_runnable += [
                {'cmd': d.EXT_SRV_CONNECT,
                 'kwargs': {'waitUntil': (lambda: True) if d.port == devices[-1].port else None},
                 } for d in devices]
        
        for u in self._tasks_runnable:
            print(f"{self.__module__} / TASKS RUNNABLE:\r\n{u}(", )
        
        self._tasks_runnable += [
                {'cmd': d.GENERAL_NOTIFICATION_REQUEST if isinstance(d, Hub) else d.REQ_PORT_NOTIFICATION,
                 'kwargs': {'waitUntil': (lambda: True) if isinstance(d, Hub) else None},
                 } for d in devices]
        self._tasks_runnable = self._tasks_runnable[:len(self._tasks_runnable)]
        
        if self._debug:
            for t in self._tasks_runnable:
                print(f"{C.BOLD}{C.OKBLUE}[{self._name}]-[MSG]:{C.ENDC}"
                      f"{t}...{C.BOLD}{C.OKBLUE}{C.UNDERLINE}\r\nDONE...{C.ENDC}")
        return self
    
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

