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
from asyncio import CancelledError, Event, Future, Task
from random import uniform

from typing import Awaitable, Callable, Optional

from colorama import Fore, Style


class Motor:
    
    def __init__(self, name: str):
        self.__name__ = name
        self._E_STALLED: Event = Event()
        self._A_ON_STALLED: Optional[Callable[[], Awaitable]] = None
        self._stall_a: int = 0
        self._stall_b: int = 0
        return
    
    @property
    def E_STALLED(self) -> Event:
        return self._E_STALLED
    
    @property
    def A_ON_STALLED(self) -> Callable[[], Awaitable]:
        return self._A_ON_STALLED
    
    @A_ON_STALLED.setter
    def A_ON_STALLED(self, action: Callable[[], Awaitable]):
        self._A_ON_STALLED = action
        return
    
    async def A_STALLED_A(self):
        self._stall_a += 1
        print(f"{Style.BRIGHT}{Fore.BLUE}\tSTALLED WITH ACTION A: {self._stall_a}", end="",  flush=True)
        # result.set_result(True)
        return
    
    async def A_STALLED_B(self):
        self._stall_b += 1
        print(f"{Style.BRIGHT}{Fore.BLUE}\tSTALLED WITH ACTION b: {self._stall_b}", end="",  flush=True)
        # result.set_result(True)
        return
    
    async def do_stall(self, for_time: float):
        
        self.E_STALLED.set()
        await asyncio.sleep(for_time)
        self.E_STALLED.clear()
        return
    
    async def start_check_stalled(self) -> Task:
        if self.A_ON_STALLED is None:
            raise Exception("no action in the event of stalling has been set")
        
        task: Task = asyncio.create_task(self.__check_stalled())
        print(f"Task: {task} scheduled to run")
        return task
    
    async def __check_stalled(self):
        """
        Check for stalling
        
        Returns
        -------

        """
        try:
            print(f"[{self.__name__}]-[MSG] has started running")
            # fut: Future = asyncio.get_running_loop().create_future()
            
            while True:
                await self.E_STALLED.wait() # wait on command begin self.
                await asyncio.sleep(0.6)
                if self.E_STALLED.is_set():
                    print(f"[{self.__name__}]-[MSG]:\t\t\t{Style.BRIGHT}{Fore.RED}STALL STALL STALL")
                    print(f"[{self.__name__}]-[MSG]:\t\t\t{Style.BRIGHT}{Fore.RED}calling {self.A_ON_STALLED.__name__}")
                    
                    await self.A_ON_STALLED()
                    continue
                else:
                    print(f"[{self.__name__}] is moving")
                    continue
        except CancelledError as ce:
            print("CHECKER CANCELLED")
        
        return True


async def main():
    # Create an Event object.
    loop = asyncio.get_event_loop()
    
    RWD: Motor = Motor("RWD")
    RWD.A_ON_STALLED = RWD.A_STALLED_A
    t = await RWD.start_check_stalled()
    
    print(f"Just starting to stall with :  {RWD.A_ON_STALLED.__name__}")
    await RWD.do_stall(5.0)
    print(f"Now switching to {RWD.A_ON_STALLED.__name__}")
    RWD.A_ON_STALLED = RWD.A_STALLED_B
    await RWD.do_stall(0.55)
    
    while True:
        await asyncio.sleep(0.001)
    

if __name__ == '__main__':
    
    asyncio.run(main())
