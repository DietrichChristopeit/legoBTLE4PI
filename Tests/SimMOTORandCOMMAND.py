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
from asyncio import Condition, Event, sleep
from random import uniform
from time import monotonic


class CMD:
    
    def __init__(self, name: str, port: int, *args, **kwargs: {}):
        self._name = name
        self._port = port
        self._args = args or []
        self._kwargs = kwargs or {}
        
        self._cmd_sent: Event = Event()
        self._cmd_sent.clear()
        return
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def cmd_sent(self) -> Event:
        return self._cmd_sent
    
    async def exec(self, m, name):
        ttc = uniform(1.00, 3.26)
        print(f"{name} STARTING COMMAND WORK FOR {ttc}")
        await sleep(ttc)
        data = f"{self._name} {self._args} {self._kwargs}"
        result = await self.send(data=data)
        await sleep(uniform(1.0, 2.5))
        m.set()
        return result
    
    async def send(self, data):
        tts: float = uniform(1.0, 2.9)
        print(f"SENDING DATA: {data}")
        try:
            print(f"SENDING IS COMPLETE IN {tts}")
            await sleep(tts)
        except ConnectionError as E_CON:
            print(f"SENDING COMMAND {data} FAILED: {E_CON.args}...")
            return E_CON
        else:
            return True


class Motor:
    
    def __init__(self, name: str, port: int):
        self._name = name
        self._port = port
        self._port_free_condition: Condition = Condition()
        self._port_free: Event = Event()
        self._port_free.set()
    
    async def CMD_MOVE(self, distance: int) -> float:
        t0 = monotonic()
        print(f"{self._name}.CMD_MOVE at GATE")
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.CMD_MOVE executing")
            cmd = await CMD('MOVE', self._port, {'distance': distance}).exec(self._port_free, self._name + '.CMD_MOVE')
            self._port_free_condition.notify_all()
        return monotonic() - t0
    
    async def CMD_SPIN(self, degrees: int) -> float:
        t0 = monotonic()
        print(f"{self._name}.CMD_SPIN at GATE")
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.CMD_SPIN executing")
            cmd = await CMD('SPIN', self._port, {'degrees': degrees}).exec(self._port_free, self._name + '.CMD_SPIN')
            self._port_free_condition.notify_all()
        return monotonic() - t0
    
    async def CMD_FLY(self, height: int) -> float:
        t0 = monotonic()
        print(f"{self._name}.CMD_FLY at GATE")
        async with self._port_free_condition:
            await self._port_free_condition.wait_for(lambda: self._port_free.is_set())
            self._port_free.clear()
            print(f"{self._name}.CMD_FLY executing")
            cmd = await CMD('FLY', self._port, {'height': height}).exec(self._port_free, self._name + '.CMD_FLY')
            self._port_free_condition.notify_all()
        return monotonic() - t0
    
    async def CMD_EXECUTED_SET(self):
        self._port_free.set()
        
        return

