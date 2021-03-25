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


class Motor:
    
    def __init__(self, name, k: int):
        self._name = name
        self._k = k
        self._wfC: Condition = Condition()
        self._E_STALLED: Event = Event()
        return
    
    @property
    def E_STALLED(self) -> Event:
        return self._E_STALLED
    
    async def setStalled(self, t):
        print(f"{self._name} sleeping {t}...")
        # await sleep(t)
        print(f"{self._name} setting Event")
        self._E_STALLED.set()
        return
    
    async def wait_until(self, cond):
        wu = True
        while wu:
            if cond():
                print(f"{self._name} met")
                wu = False
            else:
                print(f"{self._name} not met")
            await sleep(0.01)
            
        print(f"{self._name} CONDITION {cond()} met...")
        return True
    
    async def turnMotor(self, cond):
        self.E_STALLED.clear()
        loop = asyncio.get_running_loop()
        await asyncio.create_task(self.wait_until(self.E_STALLED.is_set))
        print(f"{self._name} got out...")
        return


async def main():
    loop = asyncio.get_running_loop()
    
    motor0: Motor = Motor(k=5, name='motor0')
    motor1: Motor = Motor(k=5, name='motor1')
    motor2: Motor = Motor(k=5, name='motor2')
    
    loop.call_later(2.0, motor0.setStalled, 1.0, )
    loop.call_later(3.0, motor1.setStalled, 2.0, )
    loop.call_later(5.0, motor2.setStalled, 3.0, )
    
    asyncio.create_task(motor0.turnMotor(motor0.E_STALLED.is_set))
    asyncio.create_task(motor1.turnMotor(motor1.E_STALLED.is_set))
    asyncio.create_task(motor2.turnMotor(motor2.E_STALLED.is_set))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    loop.run_forever()
