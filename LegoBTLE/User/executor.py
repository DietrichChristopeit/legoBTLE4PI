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
import asyncio
import collections
from asyncio import Condition, Future
from collections import namedtuple
from datetime import datetime
from time import monotonic
from typing import Union, final


@final
class Experiment:
    """ This class models an Experiment that can be performed with the Lego devices (Motors etc.). It is suggested to
    use this class to create and run sequences of commands concurrently.
    However, the class is mainly a wrapper with some convenience functions. Nothing stands against using
    the 'lower level' functions.

    """
    Action = namedtuple('Action', 'cmd args kwargs only_after', defaults=[None, [], {}, False])
    
    def __init__(self, name: str, measure_time: bool = False, debug: bool = False):
        """
        
        :param str name: A descriptive name.
        :param measure_time: If set, the execution time to process the Action List will be measured.
        :param debug: If set, function call info is printed.
        """
        self._savedResults: [(float, collections.defaultdict, float)] = []
        self._name = name
        self._active_actionList: [dict[Experiment.Action]] = []
        self._wait: Condition = Condition()
        self._measure_time: bool = measure_time
        self._runtime: float = -1.0
        self._experiment_results = None
        self._debug = debug
        return
    
    @property
    def name(self) -> str:
        if self._debug:
            print(f"self.name = {self._name}")
        return self._name
    
    @property
    def savedResults(self) -> list[tuple[float, collections.defaultdict, float]]:
        if self._debug:
            print(f"self.savedResults = {self._savedResults}")
        return self._savedResults
    
    @savedResults.setter
    def savedResults(self, results: tuple[float, collections.defaultdict, float]):
        if self._debug:
            print(f"savedResults({results}) = {self._savedResults}")
        self._savedResults.append(results)
        return
    
    @property
    def active_actionList(self) -> list[Action]:
        """The active Action List on which all functions run when no Action List as argument is given.

        :returns: The active Action List on which runExperiment is executed when no arguments are given.
        :rtype: list[Action]
        """
        if self._debug:
            print(f"self.active_actionList = {self._active_actionList}")
        return self._active_actionList
    
    @active_actionList.setter
    def active_actionList(self, actionList: list[Action]) -> None:
        """Sets the active Action List.

        :param list[Action] actionList: The actionList to set as active Action List.
        :return: Setter, nothing.
        :rtype: None
        """
        self._active_actionList = actionList
        return
    
    @property
    def runTime(self) -> float:
        """Returns the time needed to execute the active Action List

        :return:
        """
        return self._runtime
    
    def append(self, tasks: Union[Action, list[Action]]):
        """Appends a single Action or a list of Actions to the active list[Action].

        :param Union[Action, list[Action] tasks:
        :return: Setter, nothing.
        :rtype: None
        """
        if isinstance(tasks, Experiment.Action):
            self._active_actionList.append(tasks)
        elif isinstance(tasks, list):
            self._active_actionList.extend(tasks)
        return
    
    async def runExperiment(self, actionList: list[Action] = None, saveResults: bool = False) -> Future:
        """
        This method executes the current TaskList associated with this Experiment.

        :parameter list[Action] actionList: If provided the specified Action List will be run. Otherwise the
            active Action List will be executed (normal mode of usage).
        :parameter bool saveResults: the results of the current TaskList are stored with a Timestamp and runtime (if
            measured when executed) and can be retrieved.
        :returns: A Future that holds the current results of the Action List
        :rtype: Future
        """
        t0 = monotonic()
        
        if actionList is None:
            actionList = self._active_actionList
        
        tasks_listparts = collections.defaultdict(list)
        xc = list()
        results = collections.defaultdict(list)
        future_results = Future()
        i: int = 0
        
        for t in actionList:
            tasks_listparts[i].append(t)
            if t.only_after:
                i += 1
        print(f"EXECUTION LIST: {tasks_listparts}")
        for k in tasks_listparts.keys():
            xc.clear()
            print(f"LIST SLICE {k} executing")
            for tlpt in tasks_listparts[k]:
                task = asyncio.create_task(tlpt.cmd(*tlpt.args, **tlpt.kwargs))
                xc.append(task)
                if self._debug:
                    print(f"LIST {k}: asyncio.create_task({tlpt.cmd}({tlpt.args}))")

            results[k].append(await asyncio.wait(xc, timeout=.1))
        
        future_results.set_result(results)
        if self._measure_time:
            self._runtime = monotonic() - t0
        if saveResults:
            self.savedResults.append((datetime.timestamp(datetime.now()), results, self._runtime))
        
        self._experiment_results = future_results
        return future_results
    
    def getState(self) -> None:
        """
        This method prints an overview of the state of the experiment. It lists all tasks according to their
        (done, pending) state with results.

        :returns: Just prints put the list.
        :rtype: None
        """
        pendingTasks = list()
        for r in self._experiment_results.result():
            for ex in self._experiment_results.result()[r][0][0]:  # done tasks
                state = f"{asyncio.Task.exception(ex).args}" if asyncio.Task.exception(ex) is not None \
                    else f"HAS FINISHED WITH RESULT: {asyncio.Task.result(ex)}"
                print(f"TASK-LIST DONE {r}: Task {asyncio.Task.get_coro(ex)} {state}")
            for ex in self._experiment_results.result()[r][0][1]:  # pending tasks
                try:
                    print(
                            f"TASK-LIST PENDING {r}: Task {asyncio.Task.get_coro(ex)} {asyncio.Task.exception(ex).__str__()}")
                except asyncio.exceptions.InvalidStateError:
                    pendingTasks.append(ex)
                    print(f"TASK-LIST PENDING {r}: Task {asyncio.Task.get_coro(ex)} is WAITING FOR SOMETHING...")
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
