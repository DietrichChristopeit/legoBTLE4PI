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
from abc import ABC
from abc import ABC
from abc import abstractmethod
from asyncio import Event
from asyncio import Future
from asyncio import sleep
from random import random
from time import monotonic
from typing import Awaitable
from typing import Optional

from LegoBTLE.LegoWP.types import C


class AMotor(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def START_CHECKING(self) -> Event:
        raise NotImplementedError

    @property
    @abstractmethod
    def STALLING(self) -> Event:
        raise NotImplementedError
    
    async def STOP(self, msg: str = None):
        print(f"         {self.name}: {msg} :: STOPPING MOTOR IMMEDIATELY...")
        return f"         {self.name}: {msg} :: STOPPING MOTOR IMMEDIATELY..."
    
    async def MOVE_DEGREES(self, id: str, on_stalled: Optional[Awaitable] = None, lalles: str = 'lallels'):
        t = None
        if on_stalled is not None:
            t = asyncio.create_task(self._check_stalling(on_stalled))
        
        print(f"{id}: DOING SOMETHING ELSE... 1")
        await sleep(1)
        
        print(f"{id}: DOING SOMETHING ELSE... 2")
        try:
            await t
        except TypeError:
            print(f'{id}:\t{C.OKBLUE}{C.UNDERLINE}NO ONSTALLED{C.ENDC}')
            return False
        print(f"{C.FAIL}STALL STALL STALL{C.ENDC}")
        
        
        return True

    async def _check_stalling(self, onstalled: Optional[Awaitable]):
        t0 = monotonic()
        print(f"CHECKER :: STARTED WAITING to EXECUTE CALLBACK AT: {t0}")
        await self.START_CHECKING.wait()
        await self.STALLING.wait()
        await onstalled
        t1 = monotonic()
        print(f"CHECKER :: STOPPED WAITING for EXECUTE CALLBACK AT: {t1}")
        print(f"CHECKER :: WAITED FOR: {t1 - t0}s")
        return


class Motor(AMotor):
    
    def __init__(self, name: str, time_to_stalled: float):
        self._START_CHECKING = Event()
        self._name: str = name
        self._time_to_stalled: float = time_to_stalled
        self._STALLING: Event = Event()
        self._STALLING.clear()
        super(AMotor).__init__(Motor)
        
    @property
    def START_CHECKING(self) -> Event:
        return self._START_CHECKING
    
    @property
    def STALLING(self) -> Event:
        return self._STALLING
    
    async def set_stalled(self):
        await sleep(2.0)
        self._START_CHECKING.set()
        print(f"START CHECKING")
        while True:
            self._STALLING.clear()
            print(' ', end=' WAIT ')
            await asyncio.sleep(random() * 5.0)
            print(' ', end=' STALL ')
            self._STALLING.set()
            print(' ', end=' w ')
            await asyncio.sleep(random() * 5.0)
    
    @property
    def name(self) -> str:
        return self._name


class Auto:
    
    def __init__(self, name: str, exec: bool = True):
        self._name = name
        self._exec = exec
        return
    
    @property
    def exec(self) -> bool:
        return self._exec
    
    @exec.setter
    def exec(self, exec: bool):
        self._exec = exec
        return
    
    async def driveUntilStop(self, latestStop: int = 10, obligeStopperWait: bool = True, stopper: Optional[Awaitable] = None):
        
        for ls in range(latestStop):
            print(f"{self._name} is driving since {ls}s", end="\r")
            if stopper:
                print("is not null")
                if obligeStopperWait:
                    self.exec = True
                    await stopper
                    print("STOPPED BY STOPPER obliging wait time")
                    return
                else:
                    self.exec = False
        await stopper
        return

    async def STOP(self, name: str, waitTime: int):
        if not self.exec:
            print("I DIDN'T RUN")
            self.exec = True
            return False
        else:
            print(f"I'M STOPPING WHATEVER NOW FOR {waitTime}s...")
            await asyncio.sleep(waitTime, )
            self.exec = True
            return True
        
       
async def main():
    # m: Motor = Motor(name='TESTMOTOR', time_to_stalled=0.07)
    # t0 = monotonic()
    # t = asyncio.create_task(m.set_stalled())
    # while True:
    #     await m.MOVE_DEGREES(id='MOVE DEG1', on_stalled=None)
    #     print("MAIN: Back fromn MOVE_DEGREES")
    #     await m.MOVE_DEGREES(id='MOV_DEG2', on_stalled=m.STOP(f"STOPPING 2nd call {m.name}\r\n"))
    #     print(f"MAIN :: RUNTIME: {monotonic() - t0}")
    #     await sleep(1.3)
    # while True:  # for _ in range(1, 25):
    #     print("\t\t\t\tSTILL HERE")
    #     await asyncio.sleep(2.0)

    a = Auto("LALLES")
    print("Listen to Stopper")
    t0 = await a.driveUntilStop(latestStop=10, obligeStopperWait=True, stopper=a.STOP("EMERGENCY_STOP", 3))
    print("Ignore stoppers wait time")
    t1 = await a.driveUntilStop(latestStop=10, obligeStopperWait=False, stopper=a.STOP("EMERGENCY_STOP", 3))
    print("DONE WITH IT")
    return


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(), debug=True)
    loop.run_forever()
