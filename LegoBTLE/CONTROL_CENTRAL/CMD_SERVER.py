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

import os
import asyncio
from asyncio import AbstractEventLoop, AbstractServer
from asyncio.streams import StreamReader, StreamWriter
from collections import deque
if os.name == 'posix':
    from bluepy import btle
    from bluepy.btle import BTLEInternalError, Peripheral

from LegoBTLE.Device.messaging import Message

global host
global port
if os.name == 'posix':
    global Future_BTLEDevice

connectedDevices = {}

Q_BTLE_RETVAL: deque = deque()

if os.name == 'posix':
    class BTLEDelegate(btle.DefaultDelegate):
    
        def __init__(self, Q_HUB_CMD_RETVAL: deque):
            super().__init__()
            self._Q_BTLE_CMD_RETVAL: deque = Q_HUB_CMD_RETVAL
            return
    
        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            print(f'[BTLE]-[RCV]: [DATA] = {data.hex()}')
            M_RET = Message(data)
            if not connectedDevices == {}:
                connectedDevices[M_RET.port][1].write(M_RET.payload)
            return
    
    
    async def connectBTLE(deviceaddr: str = '90:84:2B:5E:CF:1F', host: str = '127.0.0.1', btleport: int = 9999) -> Peripheral:
        print(f'[BTLE]-[MSG]: COMMENCE CONNECT TO [{deviceaddr}]...')
        BTLE_DEVICE: Peripheral = Peripheral(deviceaddr)
        BTLE_DEVICE.withDelegate(BTLEDelegate(Q_BTLE_RETVAL))
        print(f'[{deviceaddr}]-[MSG]: CONNECTION TO [{deviceaddr}] COMPLETE...')
        return BTLE_DEVICE
    
    
    def listenBTLE(btledevice: Peripheral, loop):
        try:
            if btledevice.waitForNotifications(.005):
                print(f'Received SOMETHING FROM BTLE...')

        except BTLEInternalError:
            pass
        finally:
            loop.call_later(.01, listenBTLE, btledevice, loop)
        return


async def listen_clients(reader: StreamReader, writer: StreamWriter):
    global host
    global port
    global Future_BTLEDevice

    while True:
        try:
            message = Message(await reader.readuntil(b' '))
            addr = writer.get_extra_info('peername')
            if message.port not in connectedDevices.keys():
                connectedDevices[message.port] = (reader, writer)
            else:
                print(f'[{addr[0]}:{addr[1]}]: already connected...')
            
            print(f"Received {message.payload!r} from {addr!r}")
            ret_msg: Message = Message()
            
            if message.m_type == b'SND_SERVER_ACTION':
                if message.return_code == b'DCD':
                    print(f"DISCONNECTING DEVICE...")
                    await connectedDevices[message.port][0].close()
                    await connectedDevices[message.port][1].close()
                    connectedDevices.pop(message.port)
                if message.return_code == b'RFR':
                    ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x01')).ENCODE()
            elif message.m_type == b'SND_MOTOR_COMMAND':
                print(f"Received [{message.cmd.decode()}]:[{message.payload!r}] from {addr!r}")
                Future_BTLEDevice.writeCharacteristic(0x0e, message.payload.strip(b' '), True)
                ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x02')).ENCODE()
            elif message.m_type == b'SND_REQ_DEVICE_NOTIFICATION':
                print(f'[{host}:{port}]-[RCV]: [{message.m_type.decode()}] FOR [{message.port.hex()}]...')
                Future_BTLEDevice.writeCharacteristic(0x0e, message.payload.strip(b' '), True)
                ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x02')).ENCODE()
            connectedDevices[message.port][1].write(ret_msg.payload)
            await connectedDevices[message.port][1].drain()
            print(f"SENT [{ret_msg.return_code.decode()}]: {ret_msg.payload} to {addr}")
        except ConnectionResetError:
            print(f'CLIENTS DISCONNECTED...')
            connectedDevices.clear()
            break
            

if __name__ == '__main__':
    global host
    global port
    global server
    global Future_BTLEDevice

    loop = asyncio.get_event_loop()
    try:
        if (os.name == 'posix') and callable(connectBTLE) and  callable(listenBTLE):
            server = loop.run_until_complete(asyncio.start_server(
                    listen_clients, '127.0.0.1', 8888))
            host, port = server.sockets[0].getsockname()
            print(f'[{host}:{port}]-[MSG]: SERVER RUNNING...')
            Future_BTLEDevice = loop.run_until_complete(asyncio.ensure_future(connectBTLE()))
            loop.call_soon(listenBTLE, Future_BTLEDevice, loop)
            print(f'[CMD_SERVER]-[MSG]: BTLE CONNECTION TO [{Future_BTLEDevice.services} SET UP...')
            loop.call_soon(Future_BTLEDevice.writeCharacteristic,0x0f, b'\x01\x00', True)


        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(server.serve_forever()), ), timeout=.1))
        loop.run_forever()
    finally:
        loop.stop()
        Future_BTLEDevice.disconnect()
        loop.close()
