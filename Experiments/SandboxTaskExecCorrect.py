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
from asyncio import Condition, Event, Future, InvalidStateError, sleep

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
    
    async def send_cmd(self, value: float, result: Future = None, waitfor: bool = False):
        t0 = datetime.timestamp(datetime.now())
        print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tWAITING AT THE GATES FOR \tC...")
        if self._name == "motor2":
            print("print adding extra time")
            await sleep(20)
            print("extra time OVER")
        async with self._c:
            t_w = uniform(2.5, 4.6)
            print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tWAITING for Connection...")
            await self._connected.wait()
            print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tGOT Connection")
            print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tAT THE GATES FOR \tE...")
            await self._e.wait()
            print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tGOT C / GOT E...")
            self._e.clear()
            print(f"{self._name}/ WORKITEM {value} / PORT_VALUE: {self._port_value}:\t\tPASSED THE GATES...")
            
            # t_w = 0.0
            print(f"{self._name}/ WORKITEM {value}: WORKITEM: {value} / PORT_VALUE: {self._port_value}\tWORKING FOR {t_w}...")
            await sleep(t_w)
            print(
                f"{self._name}/ WORKITEM {value}: WORKITEM: {value} / PORT_VALUE: {self._port_value}\tDONE... Now Sending... "
                f"{datetime.timestamp(datetime.now()) - t0}")
            self._c.notify_all()
        if waitfor:
            await self._e.wait()
        result.set_result((f"{self._name}/ WORKITEM: {value} / PORT_VALUE: {self._port_value} \t\tSENT WORKITEM: {value}...",
                           datetime.timestamp(datetime.now()) - t0))
    
    def port_cmd_feedback_get(self) -> bool:
        return self._w
    
    def port_cmd_feedback_set(self, loop, w: bool):
        self._e.set()
        self._w = w
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


async def createAndRun(tl: list, loop) -> dict:
    runningTasks: list = []
    temp: list = []
    results: dict = {}
    res: dict = {}
    for t in tl:
        
        # print(f"{t[0]}({t[1]['cmdArgs']}, result={res[t[0]]})")
        try:
            try:
                await sleep(t['task']['delayBefore'])
            except KeyError:
                pass
            res[t['cmd']] = loop.create_future()
            temp.append(res[t['cmd']])
            r_task = asyncio.create_task(t['cmd'](*t.get('args', []),
                                                  **t.get('cmdArgs', {}),
                                                  result=res[t['cmd']],
                                                  waitfor=t.get('task', False).get('waitfor', False)))
            runningTasks.append(r_task)
            try:
                await sleep(t['task']['delayAfter'])
            except KeyError:
                pass
            try:
                if t.get('task', False).get('waitfor', False) or (tl.index(t) == len(tl) - 1):
                    done, pending = await asyncio.wait(temp, timeout=None)
                    for d in done:
                        print(f"RESULT IS: {d.result()}")
                    results[t['task']['name']] = [d.result() for d in done]
                    temp.clear()
            except KeyError:
                pass
        except KeyError:
            pass
    
    return results


def getResult(res, cmd):
    return res[f"{cmd}"]


async def main():
    loopy = asyncio.get_running_loop()
    
    t0 = datetime.timestamp(datetime.now())
    Motor0: Motor = Motor("motor0")
    Motor1: Motor = Motor("motor1")
    Motor2: Motor = Motor("motor2")
    
    TL = [{'cmd': Motor0.send_cmd, 'cmdArgs': {'value': 0.0}, 'task': {'name': 'Motor0LINKS', 'delayBefore': 0.0, 'delayAfter': 0.0}},
          {'cmd': Motor1.send_cmd, 'cmdArgs': {'value': 1.0}, 'task': {'name': 'Motor1VORWÄRTS'}},
          {'cmd': Motor2.send_cmd, 'cmdArgs': {'value': 2.0}, 'task': {'name': 'Motor2LINKS', 'waitfor': True, 'delayBefore': .0, 'delayAfter': .0}},
          {'cmd': Motor0.send_cmd, 'cmdArgs': {'value': 0.1}, 'task': {'name': 'Motor0RECHTS'}},
          {'cmd': Motor1.send_cmd, 'cmdArgs': {'value': 1.1}, 'task': {'name': 'Motor1RÜCKWÄRTS'}}]
    
    print(f"SENDING FEEDBACK...")
    loopy.call_soon(Motor1.port_cmd_feedback_set, loopy, True)
    loopy.call_soon(Motor0.port_cmd_feedback_set, loopy, False)
    loopy.call_soon(Motor2.port_cmd_feedback_set, loopy, True)
    
    Motor0.port_value = 15
    Motor1.connected.set()
    Motor2.connected.set()
    Motor0.connected.set()
    
    t = asyncio.create_task(createAndRun(TL, loop=loopy))
    await sleep(20)
    print(f"NOW SETTING A DIFFERENT VALUE for a Motor...")
    Motor2.port_value = 100
    while True:
        try:
            for k, v in t.result().items():
                print(f"KEY: {k}")
                for ve in v:
                    print(f"\tVALUE: {ve}")
        except InvalidStateError as ise:
            await sleep(.01)
            continue
        else:
            break
    
    Motor1.port_value = 20
    
    # while True:
    #     if not (asyncio.all_tasks().__len__() > 1):
    #         return
    #     print("------------------------")
    #     for t in asyncio.all_tasks():
    #         print(f"ASYNCIO.ALL_TASKS(): {t}")
    #     print("--------------------------")
    #     await sleep(uniform(1.0, 4.0))


if __name__ == '__main__':
    
    loopy = asyncio.get_event_loop()
    try:
        t0 = datetime.timestamp(datetime.now())
        asyncio.run(main())
        print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
        loopy.run_forever()
    except KeyboardInterrupt:
        print(f"SHUTTING DOWN...")
        loopy.run_until_complete(loopy.shutdown_asyncgens())
        loopy.stop()
        
        loopy.close()
