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
from asyncio import Condition, Future, sleep
from collections import namedtuple
from time import monotonic

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT


class Experiment:
    """
    This class models a Experiment that can be performed with the Lego devices (Motors etc.).
    
    """
    Action = namedtuple('Action', 'cmd args kwargs only_after', defaults=[None, [], {}, False])
    
    def __init__(self, name: str):
        self._name = name
        self._task_list: [dict[Experiment.Action]] = []
        self._wait: Condition = Condition()
        return
    
    def appendTask(self, task: Action) -> [Action]:
        self._task_list.append(task)
        return self._task_list
    
    def appendTaskList(self, task_list: [Action]) -> [Action]:
        self._task_list.extend(task_list)
        return self._task_list
    
    async def execute(self) -> Future:
        tasks_listparts = collections.defaultdict(list)
        xc = list()
        results = collections.defaultdict(list)
        future_results = Future()
        i: int = 0
        
        for t in self._task_list:
            tasks_listparts[i].append(t)
            if t.only_after:
                i += 1
        print(f"EXECUTION LIST: {tasks_listparts}")
        for k in tasks_listparts.keys():
            xc.clear()
            print(f"LIST slice {k} executing")
            for tlpt in tasks_listparts[k]:
                task = asyncio.create_task(tlpt.cmd(*tlpt.args, **tlpt.kwargs))
                xc.append(task)
                print(f"LIST {k}: asyncio.create_task({tlpt.cmd}({tlpt.args}))")
            # results[k].append(asyncio.as_completed(xc))
            results[k].append(await asyncio.wait(xc, timeout=.1))
        
        future_results.set_result(results)
        
        return future_results


async def main(loop):
    e: Experiment = Experiment(name='Experiment0')
    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888))
    FWD: SingleMotor = SingleMotor(name='FWD', port=b'\x01', server=('127.0.0.1', 8888), gearRatio=2.67)
    RWD: SingleMotor = SingleMotor(name='RWD', port=b'\x02', server=('127.0.0.1', 8888), gearRatio=2.67)
    STR: SingleMotor = SingleMotor(name='STR', port=b'\x00', server=('127.0.0.1', 8888), gearRatio=1.00)
    
    tl: [[e.Action]] = [e.Action(cmd=HUB.EXT_SRV_CONNECT_REQ),
                        e.Action(cmd=FWD.EXT_SRV_CONNECT_REQ),
                        e.Action(cmd=RWD.EXT_SRV_CONNECT_REQ, only_after=True),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 780}),
                        e.Action(cmd=FWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 780}),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 930}),
                        e.Action(cmd=STR.EXT_SRV_CONNECT_REQ, only_after=True),
                        e.Action(cmd=STR.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 70, 'abs_pos': 10}),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 800},
                                 only_after=True),
                        ]
    e.appendTaskList(tl)
    t0 = monotonic()
    result = await e.execute()
    
    print(f"waiting 5.0")
    await sleep(5.0)
    for r in result.result():
        for ex in result.result()[r][0][0]:
            state = f"{asyncio.Task.exception(ex).args}" if asyncio.Task.exception(ex) is not None \
                else f"HAS FINISHED WITH RESULT: {asyncio.Task.result(ex)}"
            print(f"TASK-LIST DONE {r}: Task {asyncio.Task.get_coro(ex)} {state}")
        for ex in result.result()[r][0][1]:
            try:
                print(f"TASK-LIST PENDING {r}: Task {asyncio.Task.get_coro(ex)} {asyncio.Task.exception(ex).__str__()}")
            except asyncio.exceptions.InvalidStateError:
                print(f"TASK-LIST PENDING {r}: Task {asyncio.Task.get_coro(ex)} is WAITING FOR SOMETHING")
    print(f"Overall exec took: {monotonic()-t0}")
    await sleep(.5)
    
    while True:
        await sleep(.00001)
#

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(loop=loop))
    loop.run_forever()
