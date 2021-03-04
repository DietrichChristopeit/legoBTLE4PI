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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

import asyncio
import os
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass, Field

from LegoBTLE.LegoWP.messages.upstream import EXT_SERVER_NOTIFICATION, UpStreamMessageBuilder
from LegoBTLE.LegoWP.types import HUB_SUB_COMMAND, MESSAGE_TYPE, PERIPHERAL_EVENT, SERVER_SUB_COMMAND

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
            M_RET = UpStreamMessageBuilder(data).build()
            print(f"COMMAND = {M_RET.m_event}")
            if connectedDevices != {}:  # a bit over-engineered
                connectedDevices[M_RET.m_port][1][1].write(M_RET.COMMAND[0])
                connectedDevices[M_RET.m_port][1][1].write(M_RET.COMMAND)  # a bit over-engineered
                connectedDevices[M_RET.m_port][1].drain()
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
                pass
        except BTLEInternalError:
            pass
        finally:
            loop.call_later(.01, listenBTLE, btledevice, loop)
        return


async def listen_clients(reader: StreamReader, writer: StreamWriter) -> bool:
    global host
    global port
    global Future_BTLEDevice
    addr = writer.get_extra_info('peername')
    while True:
        try:
            carrier_info: bytearray = bytearray(await reader.readexactly(n=2))
            size: int = carrier_info[1]
            handle: int = carrier_info[0]
            print(f"[{host}:{port}]-[MSG]: CARRIER SIGNAL DETECTED: handle={handle}, size={size}")
            
            CLIENT_MSG: bytearray = bytearray(await reader.readexactly(n=size))
            
            if CLIENT_MSG[3] not in connectedDevices.keys():
                # wait until Connection Request from client
                # print(f"MTYPE: {CLIENT_MSG[2] == int(M_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16)}")
                if ((CLIENT_MSG[2] != int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16))
                        or (CLIENT_MSG[4] != int(SERVER_SUB_COMMAND.REG_W_SERVER.hex(), 16))):
                    continue
                else:
                    print(f"[{host}:{port}]-[MSG]: REGISTERING DEVICE...{CLIENT_MSG[3]}")
                    connectedDevices[(CLIENT_MSG[3])] = (reader, writer)
                    print(f"[{host}:{port}]-[MSG]: CONNECTED DEVICES:\r\n {connectedDevices}")
                    cmd: bytearray = bytearray(
                            b'\x00' +
                            MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD +
                            CLIENT_MSG[3].to_bytes(1, byteorder='little', signed=False) +
                            SERVER_SUB_COMMAND.REG_W_SERVER +
                            PERIPHERAL_EVENT.EXT_SRV_CONNECTED
                        )
                    cmd = bytearray(
                        bytearray((len(cmd) + 1).to_bytes(1, byteorder='little', signed=False)) +
                        cmd
                        )
                    
                    ret_msg: EXT_SERVER_NOTIFICATION = EXT_SERVER_NOTIFICATION(cmd)
                    connectedDevices[CLIENT_MSG[3]][1].write(ret_msg.COMMAND[0].to_bytes(1, 'little', signed=False))
                    await connectedDevices[CLIENT_MSG[3]][1].drain()
                    connectedDevices[CLIENT_MSG[3]][1].write(ret_msg.COMMAND)
                    await connectedDevices[CLIENT_MSG[3]][1].drain()
                    print(f"[{host}:{port}]-[MSG]: [{addr[0]}:{addr[1]}] REGISTERED WITH SERVER...")
            else:
                print(f"[{host}:{port}]-[MSG]: [{addr[0]}:{addr[1]}]: ALREADY CONNECTED...")
                print(f"RECEIVED {CLIENT_MSG!r} FROM {addr!r}")
                
                if CLIENT_MSG[4] == SERVER_SUB_COMMAND.DISCONNECT_F_SERVER:
                    print(f"[{host}:{port}]-[MSG]: [{addr[0]}:{addr[1]}] DISCONNECTING...")
                    await connectedDevices[CLIENT_MSG[3]][0].close()
                    await connectedDevices[CLIENT_MSG[3]][1].close()
                    connectedDevices.pop(CLIENT_MSG[3])
                    print(f"[{host}:{port}]-[MSG]: [{addr[0]}:{addr[1]}] DISCONNECTED FROM SERVER...")
                    
                elif CLIENT_MSG[4] in ({v.default: k for k, v in HUB_SUB_COMMAND.__dataclass_fields__.items()}.keys()):
                    print(f"[{host}:{port}]-[MSG]: SENDING [{CLIENT_MSG}]:[{CLIENT_MSG[3]!r}] FROM {addr!r}")
                    Future_BTLEDevice.writeCharacteristic(handle, CLIENT_MSG[1:], True)
        except ConnectionResetError:
            print(f"[{host}:{port}]-[MSG]: CLIENT [{addr[0]}:{addr[1]}] RESET CONNECTION... DISCONNECTED...")
            await asyncio.sleep(.05)
            connectedDevices.clear()
            return False
        except ConnectionAbortedError:
            print(f"[{host}:{port}]-[MSG]: CLIENT [{addr[0]}:{addr[1]}] ABORTED CONNECTION... DISCONNECTED...")
            await asyncio.sleep(.05)
            connectedDevices.clear()
            return False
        continue
    return True


if __name__ == '__main__':
    global host
    global port
    global server
    global Future_BTLEDevice
    
    loop = asyncio.get_event_loop()
    try:
        server = loop.run_until_complete(asyncio.start_server(
            listen_clients, '127.0.0.1', 8888))
        host, port = server.sockets[0].getsockname()
        print(f"[{host}:{port}]-[MSG]: SERVER RUNNING...")
        if (os.name == 'posix') and callable(connectBTLE) and callable(listenBTLE):
            Future_BTLEDevice = loop.run_until_complete(asyncio.ensure_future(connectBTLE()))
            loop.call_soon(listenBTLE, Future_BTLEDevice, loop)
            print(f"[{host}:{port}]: BTLE CONNECTION TO [{Future_BTLEDevice.services} SET UP...")
            # loop.call_soon(Future_BTLEDevice.writeCharacteristic, 0x0f, b'\x01\x00', True)
        
        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(server.serve_forever()),), timeout=.1))
        loop.run_forever()
    except NameError:
        pass
    finally:
        loop.stop()
        Future_BTLEDevice.disconnect() if os.name == 'posix' else None
        loop.close()
