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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

import os
import asyncio
from asyncio.streams import StreamReader, StreamWriter

from LegoBTLE.LegoWP.messages.downstream import EXT_SRV_CONNECTED_SND
from LegoBTLE.LegoWP.messages.upstream import UpStreamMessage
from LegoBTLE.LegoWP.types import EVENT_TYPE, M_TYPE, SUB_COMMAND_TYPE, key_name

if os.name == 'posix':
    from bluepy import btle
    from bluepy.btle import BTLEInternalError, Peripheral

global host
global port
if os.name == 'posix':
    global Future_BTLEDevice

connectedDevices = {}

if os.name == 'posix':
    class BTLEDelegate(btle.DefaultDelegate):
        
        def __init__(self):
            super().__init__()
            return
        
        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            print(f'[BTLE]-[RCV]: [DATA] = {data.hex()}')
            M_RET = UpStreamMessage(data).build()
            if not connectedDevices == {}:   # a bit over-engineered
                connectedDevices[M_RET.m_port][1][1].write(M_RET.COMMAND[0])
                connectedDevices[M_RET.m_port][1][1].write(M_RET.COMMAND)  # a bit over-engineered
                await connectedDevices[M_RET.m_port][1].drain()
            return
    
    
    async def connectBTLE(deviceaddr: str = '90:84:2B:5E:CF:1F', host: str = '127.0.0.1',
                          btleport: int = 9999) -> Peripheral:
        print(f'[BTLE]-[MSG]: COMMENCE CONNECT TO [{deviceaddr}]...')
        BTLE_DEVICE: Peripheral = Peripheral(deviceaddr)
        BTLE_DEVICE.withDelegate(BTLEDelegate())
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
            carrier_info = await reader.read(2)
            handle: int = carrier_info[0]
            message_length: int = carrier_info[1]
            CLIENT_MSG = await reader.read(message_length)
            
            addr = writer.get_extra_info('peername')
            
            if CLIENT_MSG[3] not in connectedDevices.keys():
                connectedDevices[CLIENT_MSG[3]] = (reader, writer)
            else:
                print(f'[{addr[0]}:{addr[1]}]: already connected...')
            
            print(f"Received {CLIENT_MSG!r} from {addr!r}")
            
            if CLIENT_MSG[1] == M_TYPE.UPS_DNS_EXT_SERVER_CMD:
                if CLIENT_MSG[4] == SUB_COMMAND_TYPE.REG_W_SERVER:
                    print(f"REGISTERING DEVICE...")
                    connectedDevices[CLIENT_MSG[3]] = (reader, writer)
                    ret_msg: EXT_SRV_CONNECTED_SND = EXT_SRV_CONNECTED_SND(port=int.to_bytes(CLIENT_MSG[3],
                                                                                               1,
                                                                                               'little',
                                                                                               signed=False))
                    connectedDevices[CLIENT_MSG[3]][1][1].write(ret_msg.COMMAND[0])
                    connectedDevices[CLIENT_MSG[3]][1][1].write(ret_msg.COMMAND)
                    await connectedDevices[CLIENT_MSG[3]][1][1].drain()
                    print(f"DEVICE REGISTERED WITH SERVER...")
                    # await connectedDevices[CLIENT_MSG[3]][0].close()
                    # await connectedDevices[CLIENT_MSG[3]][1].close()
                    # connectedDevices.pop(CLIENT_MSG[3])
            elif CLIENT_MSG[1] == M_TYPE.UPS_DNS_GENERAL_HUB_NOTIFICATIONS:
                print(f"[{host}:{port}]-[RCV]: ["
                      f"{key_name(M_TYPE, CLIENT_MSG[1].to_bytes(1, 'little', signed=False))}] FOR ["
                      f"{CLIENT_MSG[3]}]...")
                Future_BTLEDevice.writeCharacteristic(CLIENT_MSG[0], CLIENT_MSG[1:], True)
            else:
                print(f"SENDING [{CLIENT_MSG.decode()}]:[{CLIENT_MSG[3]!r}] from {addr!r}")
                Future_BTLEDevice.writeCharacteristic(handle, CLIENT_MSG[1:], True)
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
        if (os.name == 'posix') and callable(connectBTLE) and callable(listenBTLE):
            server = loop.run_until_complete(asyncio.start_server(
                listen_clients, '127.0.0.1', 8888))
            host, port = server.sockets[0].getsockname()
            print(f'[{host}:{port}]-[MSG]: SERVER RUNNING...')
            Future_BTLEDevice = loop.run_until_complete(asyncio.ensure_future(connectBTLE()))
            loop.call_soon(listenBTLE, Future_BTLEDevice, loop)
            print(f'[CMD_SERVER]-[MSG]: BTLE CONNECTION TO [{Future_BTLEDevice.services} SET UP...')
            loop.call_soon(Future_BTLEDevice.writeCharacteristic, 0x0f, b'\x01\x00', True)
        
        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(server.serve_forever()),), timeout=.1))
        loop.run_forever()
    finally:
        loop.stop()
        Future_BTLEDevice.disconnect()
        loop.close()
