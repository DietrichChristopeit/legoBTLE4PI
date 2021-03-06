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

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.LegoWP.types import ALL_DONE, ALL_PENDING, ECMD, EVERYTHING
from LegoBTLE.networking.client import CMD_Client


class Experiment(BaseException):
    """
    This class wraps all required steps in a so called "Experiment". The user just has to specify the devices she
    wants to operate. Then with setting up command sequences and running these as Experiment the necessary connections
    are made.
    Of course all automatic setup steps can individually accessed and altered. This class is meant to make User
    definition easier and leaner.
    The automatic setup procedures assume an EXEC_Server running on 127.0.0.1:8888
    """
    
    def __init__(self,
                 devices: list[Device],
                 cmd_sequence: list[ECMD] = None,
                 cmd_client: CMD_Client = None,
                 ):
        """
        Initialize an Experiment. the bare minimum is a list of Devices that should be used in the Experiment.
        
        :param devices: A list[Device] list that holds the [Device]s used in the Experiment.
        :param cmd_sequence: Optional list[ECMD] of commands. Calling run on such an Experiment uses this command list.
        :param cmd_client: An optional command sending client. if not specified, one will be created on localhost
            connecting to localhost:8888 .
        """
        
        self._devices = devices
        self._proceed: Event = Event()
        self._cmd_sequence: list[ECMD] = cmd_sequence
        self._device_connections_installed: bool = False
        if cmd_client is None:
            self._cmd_client = CMD_Client()
        else:
            self._cmd_client = cmd_client
        return
    
    @property
    def cmd_sequence(self) -> [ECMD]:
        return self._cmd_sequence
    
    @cmd_sequence.setter
    def cmd_sequence(self, seq: [ECMD]):
        self._cmd_sequence = seq
        return
    
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
    
    async def run(self, cmd_sequence: list[ECMD], promise_max_wait: float = None,
                  expect=EVERYTHING, as_completed: bool = False) -> (bool, list[Future], list[Future], Iterator):
        
        if cmd_sequence is not None:
            seq = cmd_sequence
        else:
            seq = self._cmd_sequence
        scheduled_tasks: dict = {}
        try:
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
    
    async def connect_listen_devices_srv(self, devices: list = None,
                                         max_attempts: int = 1):
        """
        This method takes an optional devices list and tries to register the devices with the command client and make
        the client listen to any further commands from the devices.
        
        :param devices: The list of devices to connect. If not specified the list of devices at Experiment creation
            will be used.
        :param max_attempts: Optional number of max failed connection attempts.
        :return: True if successful, raise UserWarning if not.
        """
        if devices is None:
            these_devices = self._devices
        else:
            these_devices = devices
        
        connect_sequence = [ECMD(name=this_device.name, cmd=self._cmd_client.DEV_CONNECT_SRV,
                                 kwargs={'device': this_device}) for this_device in these_devices]
        
        e: UserWarning = UserWarning()
        for i in range(max_attempts):
            try:
                await self.run(connect_sequence, promise_max_wait=.3, expect=ALL_PENDING)
            except (ConnectionRefusedError, TimeoutError, ConnectionError, Exception) as e:
                continue
            else:
                return True
