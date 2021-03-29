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
from asyncio import AbstractEventLoop, Condition, InvalidStateError
from collections import defaultdict, namedtuple
from time import monotonic
from typing import List, Tuple, Union

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.LegoWP.types import bcolors


class Experiment:
    """ This class models an Experiment that can be performed with the Lego devices (Motors etc.). It is suggested to
    use this class to create and run sequences of commands concurrently.
    However, the class is mainly a wrapper with some convenience functions. Nothing stands against using
    the 'lower level' functions.
    
    :param str name: A descriptive name.
    :param measure_time: If set, the execution time to process the Action List will be measured.
    :param debug: If set, function call info is printed.

    """
    Action = namedtuple('Action', 'cmd args kwargs only_after forever_run', defaults=[None, [], defaultdict, True, False])
    
    def __init__(self, name: str, loop: AbstractEventLoop, measure_time: bool = False, debug: bool = False):
        """
        
        
        """
        self._name = name
        self._loop = loop
        self._tasks_runnable: List[defaultdict] = []
        self._wait: Condition = Condition()
        self._measure_time: bool = measure_time
        self._runtime: float = -1.0
        self._experiment_results = None
        self._savedResults: [(float, defaultdict, float)] = []
        self._debug = debug
        return
    
    @property
    def name(self) -> str:
        if self._debug:
            print(f"self.name = {self._name}")
        return self._name
    
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
    
    def runnable_tasks(self, task_list: List[dict]) -> Experiment:
        """Sets the active task List.

        :param list[dict] task_list: The actionList to set as active Action List.
        :return: Setter, nothing.
        :rtype: None
        """
        self._tasks_runnable = task_list
        return self
    
    @property
    def runTime(self) -> float:
        """Returns the time needed to execute the active Action List

        :return:
        """
        return self._runtime
    
    def append(self, tasks: Union[defaultdict, List[defaultdict]]):
        """Appends a single Action or a list of Actions to the active list[Action].
        
        Parameters
        ----------
        tasks : Union[defaultdict, list[defaultdict]
            Tasks to append.
        """
        if isinstance(tasks, defaultdict):
            self._tasks_runnable.append(tasks)
        elif isinstance(tasks, list):
            self._tasks_runnable.extend(tasks)
        return
    
    def runExperiment(self, actionList: [Action] = None, saveResults: bool = False) -> [defaultdict, float]:
        """.. py:method:async::: runExperiment(self, actionList, saveResults)
        
        This method executes the current TaskList associated with this Experiment.

        :parameter list[Action] actionList: If provided the specified Action List will be run. Otherwise the
            active Action List will be executed (normal mode of usage).
        :parameter bool saveResults: the results of the current TaskList are stored with a Timestamp and runtime (if
            measured when executed) and can be retrieved.
        :returns: A Tuple holding run Tasks and the overall runtime that holds the current results of the Action List
       
        :deprecated:
        """
        t0 = monotonic()
        
        if actionList is None:
            actionList = self._tasks_runnable
        
        tasks_listparts = defaultdict(list)
        xc = list()
        TaskList = defaultdict(list)
        i: int = 0
        
        for t in actionList:
            tasks_listparts[i].append(t)
            if t.only_after:
                i += 1
        if self._debug:
            print(f"EXECUTION LIST: {tasks_listparts}")
        for k in tasks_listparts.keys():
            xc.clear()
            if self._debug:
                print(f"LIST SLICE {k} executing")
            
            for tlpt in tasks_listparts[k]:
                task = asyncio.create_task(tlpt.cmd(*tlpt.args, **tlpt.kwargs))
                xc.append(task)
                if self._debug:
                    print(f"LIST {k}: asyncio.create_task({tlpt.cmd}({tlpt.args}))")
            if len(xc) > 0:
                TL_Part_Tasks = asyncio.create_task(asyncio.wait(xc))
            
            TaskList[k].append(xc)
        self._runtime = runtime = monotonic() - t0
        return TaskList, runtime

    async def run(self) -> defaultdict:
        """
         .. py:method::
        
        Returns:
            The results of the Experiment.

        """
        
        tasks_running: list = []
        temp: list = []
        results: defaultdict = defaultdict()
        res: defaultdict = defaultdict()
        for t in self._tasks_runnable:
            try:

                res[t['cmd']] = self._loop.create_future()
                temp.append(res[t['cmd']])
                
                if self._debug:
                    print(f"KWARGS: {kwa}" for kwa in t.get('kwargs', {}))
                  
                r_task = asyncio.create_task(t['cmd'](*t.get('args', []), **t.get('kwargs', {}),
                                                      result=res[t['cmd']],
                                                      )
                                             )
                tasks_running.append(r_task)

                if t == self._tasks_runnable[-1]:
                    if self._debug:
                        print(f"LAST TASK: {t}")
                    done, pending = await asyncio.wait(temp, timeout=None)
                    results[t['task']['tp_id']] = [d.result() for d in done]
                    break  # not really necessary
            except KeyError as ke:
                print(f"{bcolors.BOLD}{bcolors.FAIL}[{self._name}]-[MSG]:{bcolors.ENDC}"
                      f"{bcolors.UNDERLINE} KEYERROR IN EXECUTOR: {ke}{bcolors.ENDC}")
                continue
        if self._debug:
            print(f"{bcolors.BOLD}{bcolors.OKBLUE}[{self._name}]-[MSG]:{bcolors.ENDC}"
                  f"{bcolors.BOLD}{bcolors.OKBLUE}{bcolors.UNDERLINE} ASSEMBLING TASKS WITH NOTIFICATION...DONE:{bcolors.ENDC}"
                  f"{bcolors.BOLD}\r\n{*results, }{bcolors.ENDC}\r\n"
                  f"")
        return results

    def setupNotifyConnect(self, devices: List[Device]) -> Experiment:
        """This is a generator that yields the commands to connect Devices to the Server.

        Parameters
        ----------
        devices : list[Device]
            The list of devices which should be connected to the server.

        Returns
        ------
        self : Experiment
            The instance's list of runnable tasks contains defaultdict's that resemble the Tasks for each device to
            connect to the server and receive notifications.
        """
        if self._debug:
            print(f"{bcolors.BOLD}{bcolors.OKBLUE}[{self._name}]-[MSG]:{bcolors.ENDC}ASSEMBLING CONNECTION"
                  f" and NOTIFICATION Tasks...")
    
        self._tasks_runnable = [{'cmd': d.connect_ext_srv,
                                 'kwargs': {'waitUntil': (lambda: True) if d == devices[-1] else (lambda: False)},
                                 'task': {'tp_id': d.DEVNAME, }
                                 } for d in devices]
    
        self._tasks_runnable += [{'cmd': d.GENERAL_NOTIFICATION_REQUEST if isinstance(d, Hub) else d.REQ_PORT_NOTIFICATION,
                                  'kwargs': {'waitUntil': (lambda: True) if d == devices[-1] else (lambda: False)},
                                  'task': {'tp_id': d.DEVNAME, }
                                  } for d in devices]
    
        if self._debug:
            print(f"{bcolors.BOLD}{bcolors.OKBLUE}[{self._name}]-[MSG]:{bcolors.ENDC}"
                  f" {self._tasks_runnable}...{bcolors.BOLD}{bcolors.OKBLUE}{bcolors.UNDERLINE}DONE...{bcolors.ENDC}")
        return self
    
    def getState(self) -> None:
        """
        This method prints an overview of the state of the experiment. It lists all tasks according to their
        (done, pending) state with results.

        :returns: Just prints put the list.
        :rtype: None
        
        """
        pendingTasks: [] = []
        for r in self._experiment_results.result():
            for ex in self._experiment_results.result()[r][0][0]:  # done tasks
                state = f"{ex.exception().args}" if ex.exception() is not None \
                    else f"HAS FINISHED WITH RESULT: {ex.result()}"
                print(f"TASK-LIST DONE {r}: Task {ex} {state}")
            for ex in self._experiment_results.result()[r][0][1]:  # pending tasks
                try:
                    print(
                            f"TASK-LIST PENDING {r}: Task {ex} {ex.exception().__str__()}")
                except InvalidStateError:
                    pendingTasks.append(ex)
                    print(f"TASK-LIST PENDING {r}: Task {ex} is WAITING FOR SOMETHING...")
                except Exception as ce:
                    raise SystemError(f"NO CONNECTION TO SERVER... GIVING UP...{ce.args}")
        return
    
    def getDoneTasks(self):
        """
        The method returns a list of results of the done tasks.

        :returns: The done task results
        :rtype: list
        """
        res: list = []
        for r in self._experiment_results.result():
            for ex in self._experiment_results.result()[r][0][0]:  # done tasks
                res.append(ex)
        if self._debug:
            print(f"self.getDoneTasks -> {res}")
        return res
