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
from collections import Iterator
from random import uniform

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.types import ALL_DONE, ALL_PENDING, ECMD


class Experiment(BaseException):
    
    def __init__(self,
                 device_connections: {bytes: [Device, [StreamReader, StreamWriter]]} = None,
                 cmd_sequence: list[ECMD] = None,
                 loop: AbstractEventLoop = None
                 ):
        
        self.cmd_executor = None
        self._device_connections = device_connections
        self._proceed: Event = Event()
        self._cmd_sequence: list[ECMD] = cmd_sequence
        self._device_connections_installed: bool = False
        if loop is None:
            self._loop = asyncio.get_running_loop()
        else:
            self._loop = loop
        return
    
    @property
    def cmd_sequence(self) -> [ECMD]:
        return self._cmd_sequence
    
    @cmd_sequence.setter
    def cmd_sequence(self, seq: [ECMD]):
        self._cmd_sequence = seq
        return
    
    async def run(self, cmd_sequence: list[ECMD], promise_max_wait: float = None,
                  expect=ALL_DONE, as_completed: bool = False) -> (bool, list[Future], list[Future], Iterator):
        if cmd_sequence is not None:
            seq = cmd_sequence
        else:
            seq = self._cmd_sequence
        scheduled_tasks: dict = {}
        for cmd in seq:
            if callable(cmd.cmd):
                scheduled_tasks[cmd.id] = asyncio.create_task(cmd.cmd(*cmd.args or [], **cmd.kwargs or {}))
            else:
                async def f():
                    return cmd.cmd
                scheduled_tasks[cmd.id] = asyncio.create_task(f())
        if as_completed:
            return None, None, None, asyncio.as_completed(scheduled_tasks.values())
        done, pending = await asyncio.wait(scheduled_tasks.values(), timeout=promise_max_wait)
        expectation_met = True
        if expect == ALL_DONE:
            for task in scheduled_tasks.values():
                if task in done:
                    expectation_met &= True
                else:
                    raise UserWarning(f"EXPECTATION ALL_DONE VIOLATED...")
            return expectation_met, done, pending, None
        elif expect == ALL_PENDING:
            for task in scheduled_tasks.values():
                if task in pending:
                    expectation_met &= True
                else:
                    raise UserWarning(f"EXPECTATION ALL_PENDING VIOLATED...")
            return expectation_met, done, pending, None
        else:
            return None, done, pending, None
    
    async def CMD(self, cmd, result=None, args=None, wait: bool = False, proceed: Event = None) -> Future:
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
