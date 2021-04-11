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
from random import random
from typing import Awaitable
from typing import Optional


class Motor:
    
    def __init__(self, name: str, time_to_stalled: float):
        self._name: str = name
        self._time_to_stalled: float = time_to_stalled
        self._STALLING: Event = Event()
        self._STALLING.clear()
    
    async def STOP(self):
        print(f"{self._name}: STOPPING MOTOR IMMEDIATELY...")
        return
    
    async def MOVE_DEGREES(self, on_stalled: Optional[Awaitable], lalles: str = 'lallels'):
        try:
            t = asyncio.create_task(self._check_stalling(on_stalled))
        except Exception as e:
            raise e
        
        while not self._STALLING.is_set():
            await asyncio.sleep(0.001)
        print("STALL STALL STALL")
        t.cancel()
        return True
    
    async def set_stalled(self):
        while True:
            self._STALLING.clear()
            print(' ', end='W')
            await asyncio.sleep(random() * 10.0)
            print(' ', end='S')
            self._STALLING.set()
            print(' ', end='w')
            await asyncio.sleep(random() * 10.0)
            
    async def _check_stalling(self, op: Optional[Awaitable]):
        while not self._STALLING.is_set():
            await asyncio.sleep(0.001)
        else:
            await op
        return
  
  
async def main():
    
    m: Motor = Motor(name='TESTMOTOR', time_to_stalled=0.07)
    t = asyncio.create_task(m.set_stalled())
    await m.MOVE_DEGREES()
    await asyncio.sleep(5)
    print("Back fromn MOVE_DEGREES")
    
    while True: #  for _ in range(1, 25):
        print("STILL HERE")
        await asyncio.sleep(2.0)
        
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(), debug=True)
    loop.run_forever()
    