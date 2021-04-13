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
from asyncio import Event
from asyncio import Future
from random import random
from time import monotonic
from typing import Awaitable
from typing import Optional


class Motor:
    
    def __init__(self, name: str, time_to_stalled: float):
        self._name: str = name
        self._time_to_stalled: float = time_to_stalled
        self._STALLING: Event = Event()
        self._STALLING.clear()
    
    async def STOP(self, msg: str = None):
        await self._STALLING.wait()
        fut: Future = Future()
        fut.set_result(f"        {self._name}: {msg} :: STOPPING MOTOR IMMEDIATELY...")
        return f"         {self._name}: {msg} :: STOPPING MOTOR IMMEDIATELY..."
    
    async def MOVE_DEGREES(self, on_stalled: Optional[Awaitable], lalles: str = 'lallels'):
        fut = asyncio.ensure_future(on_stalled)
        try:
            t = asyncio.create_task(self._check_stalling())
        except Exception as e:
            raise e
        
        await self._STALLING.wait()
        h = await fut
        print(f"   RESULT is : {h}")
        print("    MOV_DEG  ::   STALL STALL STALL")
        t.cancel()
        return True
    
    async def _check_stalling(self, op: Optional[Awaitable] = None, msg: str = None):
        t0 = monotonic()
        print(f"CHECKER :: STARTED WAITING to EXECUTE CALLBACK AT: {t0}")
        await self._STALLING.wait()
        t1 = monotonic()
        print(f"CHECKER :: STOPPED WAITING for EXECUTE CALLBACK AT: {t1}")
        print(f"CHECKER :: WAITED FOR: {t1 - t0}s")
        return

    async def set_stalled(self):
        while True:
            self._STALLING.clear()
            print(' ', end='W')
            await asyncio.sleep(random() * 5.0)
            print(' ', end='S')
            self._STALLING.set()
            print(' ', end='w')
            await asyncio.sleep(random() * 5.0)
    
    @property
    def name(self) -> str:
        return self._name


async def main():
    m: Motor = Motor(name='TESTMOTOR', time_to_stalled=0.07)
    t0 = monotonic()
    t = asyncio.create_task(m.set_stalled())
    await m.MOVE_DEGREES(on_stalled=m.STOP(f"STOPPING 1st call: {m.name}\r\n"))
    await asyncio.sleep(5)
    print("MAIN: Back fromn MOVE_DEGREES")
    await m.MOVE_DEGREES(on_stalled=m.STOP(f"STOPPING 2nd call {m.name}\r\n"))
    await asyncio.sleep(5)
    print(f"MAIN :: RUNTIME: {monotonic() - t0}")
    while True:  # for _ in range(1, 25):
        print("\t\t\t\tSTILL HERE")
        await asyncio.sleep(2.0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(), debug=True)
    loop.run_forever()
