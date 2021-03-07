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
from asyncio.futures import Future
from collections import Iterator
from random import uniform
from typing import Optional

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.types import ALL_DONE, ALL_PENDING, ECMD, EVERYTHING
from LegoBTLE.exceptions.ValueError import NoneError
from LegoBTLE.networking.client import CMD_Client


class Experiment:
    """
    This class wraps all required steps in a so called "Experiment". The user just has to specify the devices she
    wants to operate. Then with setting up command sequences and running these as Experiment the necessary connections
    are made.
    Of course all automatic setup steps can individually accessed and altered. This class is meant to make User
    definition easier and leaner.
    The automatic setup procedures assume an EXEC_Server running on 127.0.0.1:8888
    """
    
    def __init__(self,
                 devices: Optional[list[Device]] = None,
                 cmd_client: Optional[CMD_Client] = None,
                 ):
        """
        Initialize an Experiment. the bare minimum is a list of Devices that should be used in the Experiment.
        
        :param devices: A list[Device] list that holds the [Device]s used in the Experiment.
        :param cmd_client: An optional command sending client. if not specified, one will be created on localhost
            connecting to localhost:8888 .
        """
        
        self._devices_set = False
        
        self._proceed: Event = Event()
        self._proceed.set()
        
        self._devices: list[Device] = devices
        if self._devices is not None:
            self._devices_set = True
        
        self._current_cmd_sequence: list[ECMD] = None
        
        if cmd_client is None:
            self._cmd_client: CMD_Client = CMD_Client()
        else:
            self._cmd_client = cmd_client
        
        return
    
    @property
    def devices(self) -> list[Device]:
        return self._devices
    
    @devices.setter
    def devices(self, devices: list[Device]):
        if devices is not None:
            self._devices = devices
            self._devices_set = True
        else:
            self._devices_set = False
        return
    
    @property
    def current_cmd_sequence(self) -> [ECMD]:
        return self._current_cmd_sequence
    
    @property
    def cmd_client(self):
        return self._cmd_client
    
    @cmd_client.setter
    def cmd_client(self, client: CMD_Client):
        self._cmd_client = client
        return
    
    def execute(self, cmd_sequence: list[ECMD]) -> (bool, list[Future], list[Future], Iterator):
        loop = asyncio.get_event_loop()
        expectation, done, pending, as_completed = loop.run_until_complete(self.run(cmd_sequence))
        return expectation, done, pending, as_completed
    
    async def run(self, cmd_sequence: list[ECMD],
                  promise_max_wait: Optional[float] = None,
                  expect: Optional[int] = EVERYTHING,
                  as_completed: Optional[bool] = False) -> (bool, list[Future], list[Future], Iterator):
        
        loop = asyncio.get_event_loop()
        if cmd_sequence is not None:
            self._current_cmd_sequence = cmd_sequence
        else:
            raise NoneError
        
        scheduled_tasks: dict = {}
        try:
            for cmd in self._current_cmd_sequence:
                if callable(cmd.cmd):
                    scheduled_tasks[cmd.id] = loop.run_until_complete(cmd.cmd(*cmd.args or [], **cmd.kwargs or {}))
                else:
                    async def f():
                        return cmd.cmd
                    
                    scheduled_tasks[cmd.id] = asyncio.create_task(f())
            if as_completed:
                return None, None, None, asyncio.as_completed(scheduled_tasks.values())
            done, pending = await asyncio.wait(scheduled_tasks.values(), timeout=promise_max_wait)
            
            expectation_met = True
            if expect == EVERYTHING:
                return expectation_met, done, pending, None
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
        except (ConnectionError, Exception):
            raise
    
    def connect_listen_devices_srv(self, devices: Optional[list[Device]] = None, max_attempts=3):
        """
        This method takes an optional devices list and tries to register the devices with the command client and make
        the client listen to any further commands from the devices.
        
        :param devices: The list of devices to connect. If not specified the list of devices at Experiment creation
            will be used.
        :param max_attempts: Optional number of max failed connection attempts.
        :return: True if successful, raise UserWarning if not.
        """
        loop = asyncio.get_event_loop()
        tasks = []
        future = None
        try:
            for i in range(max_attempts):
                try:
                    for d in devices:
                        tasks = [loop.create_task(self._cmd_client.DEV_LISTEN_SRV(device=d))]
                    future = asyncio.ensure_future(asyncio.wait(tasks, timeout=.1))
                    done, pending = loop.run_until_complete(future)
                except (Exception, ConnectionRefusedError) as e:
                    print(f"FUTURE: {future.exception().args}")
                    for t in tasks:
                        print(f"TASKS: {t.exception().args}")
                    for d in done:
                        print(f"DONE: {d.exception().args}")
                    print(f"GENERAL: {e.args}")
                    for p in pending:
                        print(f"DONE: {p.exception().args}")
                    print(f"GENERAL: {e.args}")
                else:
                    break
            print(done)
            print(pending)
        except Exception:
            future.exception()
        # loop = asyncio.get_event_loop()
        #
        # if (devices is None) and (self._devices is not None):
        #     these_devices = self._devices
        # else:
        #     these_devices = devices
        #
        # connect_sequence = [ECMD(name=this_device.name, cmd=self._cmd_client.DEV_CONNECT_SRV,
        #                          kwargs={'device': this_device}) for this_device in these_devices]
        # print(f"{connect_sequence}")
        # for i in range(max_attempts):
        #     try:
        #         loop.run_until_complete(asyncio.wait((asyncio.ensure_future(self.run(connect_sequence, promise_max_wait=.3, expect=ALL_PENDING)),), timeout=.1))
        #     except (ConnectionRefusedError, TimeoutError, ConnectionError, Exception):
        #         if i < max_attempts:
        #             continue
        #         else:
        #             raise
        #     else:
        #         return True
        # return True
