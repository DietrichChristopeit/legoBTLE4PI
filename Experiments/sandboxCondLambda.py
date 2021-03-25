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
from asyncio import Condition, Event, Future
from random import randint
from time import monotonic


class Motor:
    
    def __init__(self, name: str, k: int):
        self._name: str = name
        self._k = k
        self._wfC: Condition = Condition()
        self._E_STALLED: Event = Event()
        self._port_value: int = 0
        return
    
    @property
    def port_value(self) -> int:
        return self._port_value
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def E_STALLED(self) -> Event:
        return self._E_STALLED
    
    def setValue(self, t, loop):
        dt = monotonic() - t
        print(f"{self._name}-[MSG]: setValue")
        v = randint(0, 200)
        print(f"{self._name} setting value to {v}")
        self._port_value = v
        loop.call_later(0.0001, self.setValue, dt, loop)
        return
        
    def setStalled(self, t):
        dt = monotonic() - t
        print(f"[{self._name}]-[MSG]: called after {dt}...")
        print(f"{self._name} setting Event")
        self._E_STALLED.set()
        return
    
    async def wait_until(self, cond, fut: Future):
        while True:
            if cond():
                print(f"{self._name}: BREAKING...")
                print(f"{self._name} CONDITION {cond()} met...T: {monotonic()}")
                fut.set_result(True)
                return
            await asyncio.sleep(0.00001)
    
    async def turnMotor(self, cond):
        self.E_STALLED.clear()
        fut = Future()
        await self.wait_until(cond, fut)
        done, pending = await asyncio.wait((fut,), timeout=None)
        # print(f"DONE: {done}")
        # print(f"PENDING: {done}")
        print(f"{self._name} got out...T: {monotonic()}")
        return True


async def main():
    loop = asyncio.get_running_loop()
    
    motor0: Motor = Motor(k=5, name='motor0')
    motor1: Motor = Motor(k=5, name='motor1')
    motor2: Motor = Motor(k=5, name='motor2')
    
    print(f"{motor0.name}: SIMULATE STALL scheduled at: {monotonic()}...")
    # loop.call_later(2.0, motor0.setStalled, monotonic())
    # loop.call_later(3.0, motor1.setStalled, monotonic())
    # loop.call_later(5.0, motor2.setStalled, monotonic())

    loop.call_later(2.0, motor0.setValue, monotonic(), loop)
    loop.call_later(3.0, motor1.setValue, monotonic(), loop)
    loop.call_later(3.0, motor2.setValue, monotonic(), loop)
    
    t0 = asyncio.create_task(motor0.turnMotor(lambda: (motor0.port_value > 123) and (motor0.port_value < 150)))
    t1 = asyncio.create_task(motor1.turnMotor(lambda: (motor1.port_value > 10) and (motor1.port_value < 15)))
    t2 = asyncio.create_task(motor2.turnMotor(lambda: (motor2.port_value > 40) and (motor2.port_value < 50)))
    
    await t0
    await t1
    await t2
    
    return True


if __name__ == '__main__':
    
    #loop = asyncio.get_event_loop()
    # try:
    asyncio.run(main())
        #loop.stop()
        #loop.close()
    #except KeyboardInterrupt:
    #    loop.stop()
    #    loop.close()
