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
from asyncio.futures import Future
from datetime import datetime, time
from random import uniform


class Device:
    
    def __init__(self, name: str = 'device_' + str(datetime.now())):
        self._name = name
        self._connected = False
        return
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    @property
    def name(self) -> str:
        return self._name
    
    async def message(self, m) -> str:
        return self._name + f' had to sleep {m}'


class Connector:
    
    def __init__(self, devices=None, connector=None):
        if devices is None:
            devices = []
        if devices is None:
            self.dev_installed = False
            self._devices = []
        else:
            self.dev_installed = True
            self._devices = devices
        self._connector = connector
        self._connections: {
                str: (str, str)
                } = {}
        return
    
    async def connect(self, devices: [Device] = None) -> [Future]:
        loop = asyncio.get_running_loop()
        if devices is None:
            dev = self._devices
        else:
            dev = devices

        coros = {asyncio.ensure_future(self._connector(d)) for d in dev}
        
        results = await asyncio.gather(*coros, loop=loop)
        
        di = {r[0]: (r[1], r[2]) for r in results}
        # for r in results:
        # print(r)
        #  k.append({r[0]: (r[1][0], r[1][1])})
        return di


async def connect(d: Device) -> (str, str, str):
    t = uniform(1.0, 6.0)
    print(await d.message(str(t)))
    await asyncio.sleep(t)
    
    # {d.name: {'reader', 'writer'}}
    return d.name, 'reader', 'writer'


async def main():
    start = datetime.now()
    fwd: Device = Device('FWD')
    rwd: Device = Device()
    ster: Device = Device()
    
    c: Connector = Connector(connector=connect, devices=[fwd, rwd, ster])
    r = await c.connect()
    
    print(f"RESULTS: {r['FWD']}")
    print(f"It took {datetime.now() - start}")


if __name__ == '__main__':
    asyncio.run(main())
