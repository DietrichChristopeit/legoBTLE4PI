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
import contextlib
from asyncio import StreamReader, StreamWriter
from random import uniform
from time import sleep

from tornado import concurrent

from LegoBTLE.Device.TDevice import Device
from LegoBTLE.Device.TMotor import SingleMotor
from LegoBTLE.Device.messaging import Message

connectedDevices = {}


async def event_wait(evt, timeout):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def connectTo(device: Device, host: str = '127.0.0.1', port: int = 8888):
    (reader, writer) = await asyncio.open_connection(host=host, port=port)
    connectedDevices[device.DEV_PORT] = (device, (reader, writer))
    CNT_MSG: bytearray = bytearray(b'\x07\x00\x00' +
                                   connectedDevices[device.DEV_PORT][0].DEV_PORT +
                                   b'\x00\x00' +
                                   b' ')
    
    connectedDevices[device.DEV_PORT][1][1].write(CNT_MSG)
    await connectedDevices[device.DEV_PORT][1][1].drain()
    
    ret_msg = Message(await connectedDevices[device.DEV_PORT][1][0].readuntil(b' '))
    print(f'[{connectedDevices[device.DEV_PORT][0].name}]-[CNT]: [{ret_msg.return_code}]')
    return


async def MSG_SND(device: Device, msg: bytes):
    pass


async def MSG_RCV(device):
    # fut = loop.run(connectedDevices[device.DEV_PORT][1][0].readuntil(b' '))
    # RCV = Message(fut.result())
    while True:
        print(f"LISTENING FOR [{device.DEV_NAME.decode()}] FROM SERVER")
        await asyncio.sleep(uniform(.2, 1.5))


if __name__ == '__main__':
    # Creating client object
    terminate: asyncio.Event = asyncio.Event()
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67, terminate=terminate)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67, terminate=terminate)
    STR = SingleMotor(name="STR", port=b'\x02', gearRatio=2.67, terminate=terminate)
    loop = asyncio.get_event_loop()
    
    tasks = [
        asyncio.ensure_future(connectTo(RWD, '127.0.0.1', 8888)),
        asyncio.ensure_future(MSG_RCV(FWD)),
        asyncio.ensure_future(MSG_RCV(RWD)),
        asyncio.ensure_future(MSG_RCV(STR)),
        asyncio.ensure_future(connectTo(FWD, '127.0.0.1', 8888)),
        asyncio.ensure_future(connectTo(STR, '127.0.0.1', 8888))
        ]
    loop.run_until_complete(asyncio.wait(tasks, timeout=0.9))
    loop.run_until_complete(asyncio.sleep(5.0))
    print("HALLO")
    loop.run_forever()
