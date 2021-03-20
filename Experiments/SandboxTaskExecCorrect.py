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
from asyncio import Condition, Event, Future, sleep
from datetime import datetime
from random import uniform


class Motor:
    
    def __init__(self, name):
        self._connected = Event()
        self._connected.clear()
        self._port_value: int = None
        self._name = name
        self._c = Condition()
        self._e = Event()
        self._e.clear()
        self._w = False
    
    async def send_cmd(self, value: float, result: Future = None):
        t0 = datetime.timestamp(datetime.now())
        print(f"{self._name}/ WORKITEM {value}:\t\tWAITING AT THE GATES FOR \tC...")
        if self._name == "motor2":
            print("print adding extra time")
            await sleep(20)
            print("extra time OVER")
        async with self._c:
            t_w = uniform(2.5, 4.6)
            print(f"{self._name}/ WORKITEM {value}:\t\tWAITING for Connection...")
            await self._connected.wait()
            print(f"{self._name}/ WORKITEM {value}:\t\tGOT Connection")
            print(f"{self._name}/ WORKITEM {value}:\t\tAT THE GATES FOR \tE...")
            await self._e.wait()
            print(f"{self._name}/ WORKITEM {value}:\t\tGOT C / GOT E...")
            self._e.clear()
            print(f"{self._name}/ WORKITEM {value}:\t\tPASSED THE GATES...")
            
            
            # t_w = 0.0
            print(f"{self._name}/ WORKITEM {value}: WORKITEM: {value}\tWORKING FOR {t_w}...")
            await sleep(t_w)
            print(f"{self._name}/ WORKITEM {value}: WORKITEM: {value}\tDONE... Now Sending... {datetime.timestamp(datetime.now()) - t0}")
            self._c.notify_all()
        await self._e.wait()
        result.set_result((f"{self._name}/ WORKITEM: {value}:\t\tSENT WORKITEM: {value}...", datetime.timestamp(datetime.now()) - t0))
    
    def port_cmd_feedback_get(self) -> bool:
        return self._w
    
    def port_cmd_feedback_set(self, loop, w: bool):
        self._e.set()
        self._w = w
        # print(f"{self._name}: EVENT set to True")
        loop.call_later(uniform(0.01, 0.05), self.port_cmd_feedback_set, loop, w)
        return
    
    @property
    def connected(self) -> Event:
        print(f"{self._name}: CONNECTED IS SET")
        return self._connected
    
    @property
    def port_value(self) -> int:
        return self._port_value
    
    @port_value.setter
    def port_value(self, value: int):
        self._port_value = value
        return


async def createAndRun(tl: list, loop) -> list:
    runningTasks: list = []
    temp = []
    results = []
    res: dict = {}
    for t in tl:
        
        # print(f"{t[0]}({t[1]['cmdArgs']}, result={res[t[0]]})")
        try:
            try:
                await sleep(t[2]['task']['delayBefore'])
            except KeyError:
                pass
            res[t[0]] = loop.create_future()
            temp.append(res[t[0]])
            r_task = asyncio.create_task(t[0](t[1]['cmdArgs']['value'], result=res[t[0]]))
            runningTasks.append(r_task)
            try:
                await sleep(t[2]['task']['delayAfter'])
            except KeyError:
                pass
            try:
                if t[2]['task']['waitFor'] or (tl.index(t) == len(tl)-1):
                    done = await asyncio.wait(temp, timeout=None)
                    print(f"RESULT IS: {done}")
                    results.append(done)
                    temp.clear()
            except KeyError:
                pass
        except KeyError:
            pass
        
    return results


def getResult(res, cmd):
    return res[f"{cmd}"]


async def main(loop):
    loopy = asyncio.get_running_loop()
    
    t0 = datetime.timestamp(datetime.now())
    Motor0: Motor = Motor("motor0")
    Motor1: Motor = Motor("motor1")
    Motor2: Motor = Motor("motor2")
  
    TL = [[Motor0.send_cmd, {'cmdArgs': {'value': 0.0}}, {'task': {'name': 'Motor0 LINKS', 'delayBefore': 0.0, 'delayAfter': 0.0}}],
          [Motor1.send_cmd, {'cmdArgs': {'value': 1.0}}, {'task': {'name': 'Motor1 VORWÄRTS'}}],
          [Motor2.send_cmd, {'cmdArgs': {'value': 2.0}}, {'task': {'name': 'Motor2 LINKS', 'waitFor': True, 'delayBefore': 2.0, 'delayAfter': .0}}],
          [Motor0.send_cmd, {'cmdArgs': {'value': 0.1}}, {'task': {'name': 'Motor0 RECHTS'}}],
          [Motor1.send_cmd, {'cmdArgs': {'value': 1.1}}, {'task': {'name': 'Motor1 RÜCKWÄRTS'}}],
          ]
    print(f"SENDING FEEDBACK...")
    loopy.call_soon(Motor1.port_cmd_feedback_set, loopy, True)
    loopy.call_soon(Motor0.port_cmd_feedback_set, loopy, False)
    loopy.call_soon(Motor2.port_cmd_feedback_set, loopy, True)

    Motor0.port_value = 15
    Motor1.connected.set()
    Motor2.connected.set()
    Motor0.connected.set()
    Motor1.port_cmd_feedback_set(loopy, True)
    Motor0.port_cmd_feedback_set(loopy, False)
    Motor2.port_cmd_feedback_set(loopy, True)
    results = await createAndRun(TL, loop=loopy)
    Motor1.port_cmd_feedback_set(loopy, True)
    Motor0.port_cmd_feedback_set(loopy, False)
    Motor2.port_cmd_feedback_set(loopy, True)
    print(f"SLEEPING 20...")
    await sleep(10.0)
    Motor1.port_value = 20
    
    # print(f"\n\nOVERALL RUNTIME: \t{datetime.timestamp(datetime.now())-t0}")
    
    while True:
        if not (asyncio.all_tasks().__len__() > 1):
            return
        print("------------------------")
        for t in asyncio.all_tasks():
            print(f"ASYNCIO.ALL_TASKS(): {t}")
        print("--------------------------")
        # Motor1.port_cmd_feedback_set(loopy, True)
        # Motor0.port_cmd_feedback_set(loopy, False)
        # Motor2.port_cmd_feedback_set(loopy, True)
        await sleep(uniform(1.0, 4.0))
        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    t0 = datetime.timestamp(datetime.now())
    asyncio.run(main(loop))
    print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
    loop.run_forever()
