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

from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Device.TDevice import Device
from LegoBTLE.Device.TMotor import SingleMotor
from LegoBTLE.Device.messaging import Message

connectedDevices = {}


async def event_wait(evt, timeout):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def DEV_CONNECT(device: Device, host: str = '127.0.0.1', port: int = 8888):
    connectedDevices[device.DEV_PORT] = (device, (await asyncio.open_connection(host=host, port=port)))
    CNT_MSG: bytearray = bytearray(b'\x07\x00\x00' +
                                   connectedDevices[device.DEV_PORT][0].DEV_PORT +
                                   b'\x00\x00' +
                                   b' ')
    
    connectedDevices[device.DEV_PORT][1][1].write(CNT_MSG)
    await connectedDevices[device.DEV_PORT][1][1].drain()
    
    ret_msg = Message(await connectedDevices[device.DEV_PORT][1][0].readuntil(b' '))
    print(f'[{connectedDevices[device.DEV_PORT][0].name}]-[CNT]: [{ret_msg.return_code.decode()}]')
    return


async def DEV_DISCONNECT(device: Device, host: str = '127.0.0.1', port: int = 8888) -> bool:
    CNT_MSG: bytearray = bytearray(b'\x07\x00\x00' +
                                   connectedDevices[device.DEV_PORT][0].DEV_PORT +
                                   b'\x00\xff' +
                                   b' ')

    connectedDevices[device.DEV_PORT][1][1].write(CNT_MSG)
    await connectedDevices[device.DEV_PORT][1][1].drain()
    connectedDevices.pop(device.DEV_PORT)
    return True


async def CMD_SND1(fun, *args):
    fun(*args)
    # afterwards: await CMD_SND1(device.turnForT, (5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK))
    
    
async def CMD_SND(device: Device, msg: bytes) -> bytes:
    
    if isinstance(device, SingleMotor):
        cmd = device.turnForT(5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK)
        print(cmd.payload + b' ')
    else:
        cmd = Message(b'')
    print(connectedDevices[device.DEV_PORT][1][1].get_extra_info('peername'))
    connectedDevices[device.DEV_PORT][1][1].write(cmd.payload + b' ')
    await connectedDevices[device.DEV_PORT][1][1].drain()
    
    return cmd.payload + b' '


async def MSG_RCV(device):
    while True:
        try:
            print(f"[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
            msg_rcv = Message(await connectedDevices[device.DEV_PORT][1][0].readuntil(b' '))
            print(f"[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[{msg_rcv.return_code.decode()}]: [DATA] = ["
                  f"{msg_rcv.payload}]")
        except ConnectionResetError:
            print(f'[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[MSG]: DEVICE DISCONNECTED...')
            connectedDevices.pop(device.DEV_PORT)
            break
    return

if __name__ == '__main__':
    
    def INIT() -> list:
        return [
            asyncio.ensure_future(DEV_CONNECT(RWD)),
            asyncio.ensure_future(DEV_CONNECT(FWD)),
            asyncio.ensure_future(DEV_CONNECT(STR)),
            ]
    
    def LISTEN_DEV() -> list:
        return [
            asyncio.ensure_future(MSG_RCV(FWD)),
            asyncio.ensure_future(MSG_RCV(RWD)),
            asyncio.ensure_future(MSG_RCV(STR))
            ]
    
    # Creating client object
    terminate: asyncio.Event = asyncio.Event()
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67, terminate=terminate)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67, terminate=terminate)
    STR = SingleMotor(name="STR", port=b'\x02', gearRatio=2.67, terminate=terminate)
    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(asyncio.wait(INIT()))
    loop.run_until_complete(asyncio.wait(LISTEN_DEV(), timeout=0.9))
    
    # CMDs come here
    
    loop.run_until_complete(asyncio.sleep(5.0))
    loop.run_until_complete(CMD_SND(STR, b''))
    loop.run_until_complete(CMD_SND(FWD, b''))
    print("HALLO")
    loop.run_until_complete(CMD_SND(RWD, b''))
    loop.run_forever()
