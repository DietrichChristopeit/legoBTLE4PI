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

from LegoBTLE.LegoWP.types import C
from curses import wrapper


class Motor:
    
    def __init__(self, name: str, k: int, time_to_stall: float = 0.1, stall_bias: int = 3):
        self._name: str = name
        self._rn = k * "\r\n"
        self._time_to_stall: float = time_to_stall
        self._stall_bias: int = stall_bias
        self._last_stall_status: bool = False
        self._E_STALLED: Event = Event()
        self._E_CMD_RUNNING: Event = Event()
        self._wfC: Condition = Condition()
        self._port_value: int = 0
        
        return
    
    async def _watch_stalling(self):
        print(f"{self._rn} RES. {self.name}:\r\n")
        txt0 = f"{C.BOLD}{C.OKGREEN}{self._name}: {C.FAIL}STALLED\tDelta:"
        txt1 = f"{C.BOLD}{C.OKGREEN}{self._name}: {C.OKBLUE}FREE\tDelta:"
        lasttxt = f""
        while True:
            m0: int = self._port_value
            await asyncio.sleep(self._time_to_stall)
            delta = abs(self._port_value - m0)

            if (delta < self._stall_bias) and self._E_CMD_RUNNING.is_set():
                if self._last_stall_status != self._E_STALLED.is_set():
                    lasttxt = txt0
            
                self._E_STALLED.set()
            elif (delta >= self._stall_bias) and self._E_CMD_RUNNING.is_set():
                if self._last_stall_status != self._E_STALLED.is_set():
                    lasttxt = txt1
                self._E_STALLED.clear()
            else:
                if self._last_stall_status != self._E_STALLED.is_set():
                    lasttxt = txt1
                self._E_STALLED.clear()
            print(f"{lasttxt} {delta}{C.ENDC}", end=",", flush=True)
            self._last_stall_status = self._E_STALLED.is_set()

    @property
    def port_value(self) -> int:
        return self._port_value
    
    @port_value.setter
    def port_value(self, port_value: int):
        self._port_value = port_value
        return
    
    @property
    def time_to_stall(self) -> float:
        return self._time_to_stall
    
    @time_to_stall.setter
    def time_to_stall(self, time: float):
        self._time_to_stall = time
        return
    
    @property
    def stall_bias(self) -> int:
        return self._stall_bias
    
    @stall_bias.setter
    def stall_bias(self, stall_bias: int):
        self._stall_bias = stall_bias
        return

    @property
    def E_STALLED(self) -> Event:
        return self._E_STALLED
        
    @property
    def E_CMD_RUNNING(self) -> Event:
        return self._E_CMD_RUNNING
    
    @property
    def name(self) -> str:
        return self._name
    
    async def setValue_forever(self):
        while True:
            v = randint(0, 20000)
            # print(f"{self._name} setting value to {v}")
            await asyncio.sleep(0.001)
            self._port_value = v

    async def setValue(self):
        while True:
            v = randint(0, 20000)
            # print(f"{self._name} setting value to {v}")
            await asyncio.sleep(0.001)
            self._port_value = v
    
    async def wait_until(self, cond, fut: Future):
        while True:
            if cond():
                print(f"{self._name}: BREAKING...")
                print(f"{self._name} CONDITION {cond()} met...T: {monotonic()}")
                fut.set_result(True)
                return
            await asyncio.sleep(0.00001)
    
    async def turnMotor(self, cond=None):
        
        self._E_CMD_RUNNING.set()
        for i in range(0, randint(10000, 20000)):
            self.port_value = i
            await asyncio.sleep(0.001)
        self._E_CMD_RUNNING.clear()
        
        return True


async def main():
    loop = asyncio.get_running_loop()
    
    motor0: Motor = Motor(k=2, name='motor0', time_to_stall=0.1, stall_bias=12)
    motor1: Motor = Motor(k=4, name='motor1', time_to_stall=0.1, stall_bias=9)
    motor2: Motor = Motor(k=6, name='motor2', time_to_stall=0.1, stall_bias=25)

    # noinspection PyProtectedMember
    stall_watcher0 = asyncio.create_task(motor0._watch_stalling())
    # noinspection PyProtectedMember
    stall_watcher1 = asyncio.create_task(motor1._watch_stalling())
    # noinspection PyProtectedMember
    stall_watcher2 = asyncio.create_task(motor2._watch_stalling())
    
    t0 = asyncio.create_task(motor0.turnMotor())
    t1 = asyncio.create_task(motor1.turnMotor())
    t2 = asyncio.create_task(motor2.turnMotor())
    
    await t0
    await t1
    await t2
    
    return True


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    # try:
    asyncio.run(main())
        #loop.stop()
        #loop.close()
    #except KeyboardInterrupt:
    #    loop.stop()
    #    loop.close()
