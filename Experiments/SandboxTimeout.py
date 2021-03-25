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
from random import getrandbits, randint, uniform
from time import monotonic


class Motor:
    
    def __init__(self, cto: float, name: str = "LALLES0", debug: bool=False):
        self._timeout = cto
        self._port_free_cond: Condition = Condition()
        self._port_free: Event = Event()
        self._command_started: Event = Event()
        self._E_MOTOR_STALLED: Event = Event()
        self._port_free.set()
        self._E_stalled: Event = Event()
        self._name = name
        self._pos: int = 1
        self._last_pos: int = 0
        self._unchanged: int = -1
        self._unchanging: bool = False
        self._debug: bool = debug
        return
    
    @property
    def debug(self) -> bool:
        return self._debug
    
    @property
    def E_MOTOR_STALLED(self) -> Event:
        return self._E_MOTOR_STALLED
    
    async def turnMotor(self, period: int):
        async with self._port_free_cond as pfc:
            await self._port_free.wait()
            self._port_free.clear()
            self._E_MOTOR_STALLED.clear()
            loop = asyncio.get_running_loop()
            h = loop.call_soon(self.check_stalled_cond, loop, self._pos, None, 2.5)
            await self.send(period)
            h.cancel()
            self._port_free_cond.notify_all()
        return
    
    def check_stalled_cond(self, loop, last_val, last_val_time: float = 0.0, timeout: float = None):
        if last_val_time is None:
            last_val_time = monotonic()
        # print(f"{self._name} CALLED CHECKSTALLING...")
        if self._pos == last_val:
            if (monotonic() - last_val_time) >= timeout:
                if self.debug:
                    print(f"{self._name} STALLED....")
                self.E_MOTOR_STALLED.set()
                return
        elif self._pos != last_val:
            if self.debug:
                print(f"{self._name}: OK")
            last_val = self._pos
            last_val_time = monotonic()
        loop.call_later(.0001, self.check_stalled_cond, loop, last_val, last_val_time, timeout)
        return
    
    async def send(self, p: int):
        period = p * 100
        self.E_MOTOR_STALLED.clear()
        while (period > 0) and (not self.E_MOTOR_STALLED.is_set()):
            period -= 1
            await sleep(.001)
            self.pos = randint(1, 200)
            if bool(getrandbits(1)):
                if self.debug:
                    print(f"{self._name} POSITION unchanged: {self._pos}")
                ts = uniform(2.0, 2.6)
                if self.debug:
                    print(f"{self._name}... SELLEPING NOW: {ts}...")
                await sleep(ts)
                continue
            else:
                if self.debug:
                    print(f"{self._name} POSITION changed: {self._pos}")
                await sleep(.001)
        if self.E_MOTOR_STALLED.is_set():
            ret = f"{self._name}.turnMotor STALLED..."
        else:
            ret = f"{self._name}.turnMotor DID NOT STALL..."
        self.E_MOTOR_STALLED.clear()
        self._port_free.set()
        
        return ret
    
    @property
    async def pos(self) -> int:
        return self._pos
    
    @pos.setter
    def pos(self, pos: int):
        self._last_pos = self._pos
        self._pos = pos
        return
    

async def main():
    # async with timeout(10.0) as cm:
    
    motor1: Motor = Motor(cto=2.0, name='Motor1', debug=True)
    motor2: Motor = Motor(cto=2.0, name='Motor2', debug=True)
    motor3: Motor = Motor(cto=2.0, name='Motor3', debug=True)
    
    sendT = [asyncio.create_task(motor1.turnMotor(20)),
             asyncio.create_task(motor2.turnMotor(20)),
             asyncio.create_task(motor3.turnMotor(20)),
             ]
    done, pending = await asyncio.wait(sendT, timeout=25.0)
    
    print(f"DONE: {done}")
    for d in done:
        print(f"DONE: {d.result()}")
    
    for p in pending:
        print(f"PENDING: {p}")
    return


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        asyncio.run(main())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
    finally:
        loop.close()
