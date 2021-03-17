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
from asyncio import Condition, Event, sleep
from datetime import datetime
from random import uniform


class Motor:
    
    def __init__(self, name):
        self._port_value: int = None
        self._name = name
        self._c = Condition()
        self._e = Event()
        self._e.clear()
        self._w = False
    
    async def send_cmd(self, i: float):
        t0 = datetime.timestamp(datetime.now())
        print(f"{self._name}/ WORKITEM {i}:\t\tWAITING AT THE GATES FOR \tC...")
        async with self._c:
            print(f"{self._name}/ WORKITEM {i}:\t\tAT THE GATES FOR \tE...")
            await self._e.wait()
            print(f"{self._name}/ WORKITEM {i}:\t\tGOT C / GOT E...")
            self._e.clear()
            print(f"{self._name}/ WORKITEM {i}:\t\tPASSED THE GATES...")
            
            t_w = uniform(2.5, 4.6)
            print(f"{self._name}/ WORKITEM {i}: WORKITEM: {i}\tWORKING FOR {t_w}...")
            await sleep(t_w)
            print(f"{self._name}/ WORKITEM {i}: WORKITEM: {i}\tDONE... Now Sending...")
            self._c.notify_all()
        return f"{self._name}/ WORKITEM: {i}:\t\tSENT WORKITEM: {i}...", datetime.timestamp(datetime.now()) - t0
    
    def port_cmd_feedback_get(self) -> bool:
        return self._w
    
    async def port_cmd_feedback_set(self, w: bool):
        if w:
            self._e.set()
            self._w = w
            print(f"{self._name}: EVENT set to True")
        return
    
    @property
    def port_value(self) -> int:
        return self._port_value
    
    @port_value.setter
    def port_value(self, value: int):
        self._port_value = value
        return


def createAndRun(tl: list) -> list:
    runningTasks: list = []
    
    for t in tl:
        runningTasks.append(asyncio.create_task(t['cmd'](t['args'])))
    return runningTasks


async def main(loop):
    t0 = datetime.timestamp(datetime.now())
    Motor0: Motor = Motor("motor0")
    Motor1: Motor = Motor("motor1")
    Motor2: Motor = Motor("motor2")
  
    TL = [{'name': 'Motor0 LINKS', 'cmd': Motor0.send_cmd, 'args': 0.0},
          {'name': 'Motor1 VORWÄRTS', 'cmd': Motor1.send_cmd, 'args': 1.0},
          {'name': 'Motor2 LINKS', 'cmd': Motor2.send_cmd, 'args': 2.0},
          {'name': 'Motor0 RECHTS', 'cmd': Motor0.send_cmd, 'args': 0.1},
          {'name': 'Motor1 RÜCKWÄRTS', 'cmd': Motor1.send_cmd, 'args': 1.1},
          ]
    
    running = createAndRun(TL)
    Motor0.port_value = 15
    
    await sleep(uniform(1.0, 1.0))
    await Motor1.port_cmd_feedback_set(True)
    await Motor0.port_cmd_feedback_set(True)
    
    await sleep(uniform(1.0, 1.0))
    Motor1.port_value = 20
    await Motor2.port_cmd_feedback_set(True)
    await Motor0.port_cmd_feedback_set(True)
    await Motor1.port_cmd_feedback_set(True)
    # done, pending = \
    done, pending = await asyncio.wait(running, timeout=20.0)
    
    for t in done:
        print(f"DONE:", t.result()[0], t.result()[1])
    
    for t in asyncio.all_tasks():
        print(f"ASYNCIO.ALL_TASKS(): {t}")
    print(f"\n\nOVERALL RUNTIME: \t{datetime.timestamp(datetime.now())-t0}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(loop))
    loop.run_forever()
