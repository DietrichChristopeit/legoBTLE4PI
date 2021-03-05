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
from asyncio import AbstractEventLoop, Event, StreamReader, StreamWriter
from asyncio.futures import Future
from random import uniform

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.messages.downstream import DOWNSTREAM_MESSAGE
from LegoBTLE.LegoWP.types import ALL_DONE, ALL_PENDING, EXPECTATION, PCMD


class CMD_SPlayer(BaseException):
    
    def __init__(self,
                 device_connections: {bytes: [Device, [StreamReader, StreamWriter]]} = None,
                 cmd_sequence: list[PCMD] = None,
                 loop: AbstractEventLoop = None
                 ):
        
        self.cmd_executor = None
        self._device_connections = device_connections
        self._proceed: Event = Event()
        self._cmd_sequence: list[PCMD] = cmd_sequence
        self._device_connections_installed: bool = False
        if loop is None:
            self._loop = asyncio.get_running_loop()
        else:
            self._loop = loop
        return
    
    @property
    def cmd_sequence(self) -> [PCMD]:
        return self._cmd_sequence
    
    @cmd_sequence.setter
    def cmd_sequence(self, seq: [PCMD]):
        self._cmd_sequence = seq
        return
    
    async def play_sequence(self, cmd_sequence: list[PCMD], promise_max_wait: float = None,
                            return_when=ALL_DONE) -> (bool, list[Future], list[Future]):
        if cmd_sequence is not None:
            seq = cmd_sequence
        else:
            seq = self._cmd_sequence
        scheduled_tasks: dict = {}
        for cmd in seq:
            scheduled_tasks[cmd.id] = asyncio.create_task(cmd.cmd(*cmd.args or [], **cmd.kwargs or []))
        done, pending = await asyncio.wait(scheduled_tasks.values(), timeout=promise_max_wait)
        expectation_met = True
        if return_when == ALL_DONE:
            for task in scheduled_tasks.values():
                if task in done:
                    expectation_met &= True
                else:
                    raise UserWarning(f"EXPECTATION ALL_DONE VIOLATED...")
            return expectation_met, done, pending
        elif return_when == ALL_PENDING:
            for task in scheduled_tasks.values():
                if task in pending:
                    expectation_met &= True
                else:
                    raise UserWarning(f"EXPECTATION ALL_PENDING VIOLATED...")
            return expectation_met, done, pending
        else:
            return None, done, pending
    
    async def exec_get_result(self,
                              cmd: DOWNSTREAM_MESSAGE,
                              resultfrom=None,
                              *result_args,
                              wait: bool = False) -> Future:
        r = Future()
        await self._proceed.wait()
        if wait:
            self._proceed.clear()
            self.cmd_executor()
        
        else:
            dt = uniform(3.0, 3.0)
            print(f"{cmd}:WAITING {dt}...")
            await asyncio.sleep(dt)
        if result is None:
            r.set_result(True)
        else:
            if result_args is None:
                raise ReferenceError(f"The parameter c_args is None whereas result-cmd is {result}...")
            r.set_result(result(*result_args))
        return r
    
    async def CMD(cmd, result=None, args=None, wait: bool = False, proceed: Event = None) -> Future:
        r = Future()
        print(f"EXECUTING CMD: {cmd!r}")
        if proceed is None:
            proceed = Event()
            proceed.set()
        
        await proceed.wait()
        if wait:
            proceed.clear()
            print(f"{cmd}: WAITING 5.0 FOR EXEC COMPLETE...")
        else:
            t = uniform(.01, .09)
            print(f"{cmd}: WAITING {t} FOR EXEC COMPLETE...")
            await asyncio.sleep(t)
        if result is None:
            r.set_result(True)
        else:
            r.set_result(result(*args))
        print(f"{cmd}: EXEC COMPLETE...")
        return r
