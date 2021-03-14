# coding=utf-8
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

from LegoBTLE.LegoWP.messages.upstream import EXT_SERVER_NOTIFICATION, UpStreamMessageBuilder
from LegoBTLE.LegoWP.types import MESSAGE_TYPE, PERIPHERAL_EVENT, SERVER_SUB_COMMAND

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
        
        def handleNotification(self, cHandle, data: bytearray):  # Eigentliche Callbackfunktion
            print(f"Returned NOTIFICATION = {data.hex()}")
            try:
                M_RET = UpStreamMessageBuilder(data).build()
            except TypeError as te:
                print(f"Wrong answer from BTLE... IGNORING...\r\n\t{te.args}")
                return
            if connectedDevices != {}:  # a bit over-engineered
                try:
                    connectedDevices[M_RET.m_port][1].write(M_RET.m_header.m_length)
                    connectedDevices[M_RET.m_port][1].write(M_RET.data)  # a bit
                    # over-engineered
                    # connectedDevices[int(M_RET.m_port.hex(), 16)][1].drain()
                except KeyError as ke:
                    print(f"PORT {data[3]} not a connected Client...ignoring...")
            return
    
    
    async def connectBTLE(deviceaddr: str = '90:84:2B:5E:CF:1F', host: str = '127.0.0.1',
                          btleport: int = 9999) -> Peripheral:
        """Establish the Lego(c) Hub <-> Computer bluetooth connection.

        :param btleport: The server port.
        :type btleport: int
        :param host: The hostname.
        :type host: str
        :param deviceaddr: The MAC Address of the Lego(c) Hub.
        :type deviceaddr: str
        """
        print(f'[BTLE]-[MSG]: COMMENCE CONNECT TO [{deviceaddr}]...')
        BTLE_DEVICE: Peripheral = Peripheral(deviceaddr)
        BTLE_DEVICE.withDelegate(BTLEDelegate())
        print(f'[{deviceaddr}]-[MSG]: CONNECTION TO [{deviceaddr}] COMPLETE...')
        return BTLE_DEVICE
    
    
    def listenBTLE(btledevice: Peripheral, loop):
        try:
            if btledevice.waitForNotifications(.005):
                print(f"Notification")
        except BTLEInternalError:
            pass
        loop.call_later(.01, listenBTLE, btledevice, loop)
        return


async def listen_clients(reader: StreamReader, writer: StreamWriter) -> bool:
    global host
    global port
    global Future_BTLEDevice
    conn_info = writer.get_extra_info('peername')
    while True:
        CLIENT_MSG: bytearray = None
        try:
            carrier_info: bytearray = bytearray(await reader.readexactly(n=2))
            size: int = carrier_info[1]
            handle: int = carrier_info[0]
            print(f"[{host}:{port}]-[MSG]: CARRIER SIGNAL DETECTED: handle={handle}, size={size}")
            
            CLIENT_MSG: bytearray = bytearray(await reader.readexactly(n=size))
            
            if handle == 15:
                print(f"[{host}:{port}]-[MSG]: SENDING: {handle}, {CLIENT_MSG[1:]} FROM {conn_info!r}")
                if os.name == 'posix':
                    Future_BTLEDevice.writeCharacteristic(0x0f, b'\x01\x00', True)
                continue
            
            if CLIENT_MSG[3:4] not in connectedDevices.keys():
                # wait until Connection Request from client
                if ((CLIENT_MSG[2] != int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16))
                        or (CLIENT_MSG[4] != int(SERVER_SUB_COMMAND.REG_W_SERVER.hex(), 16))):
                    continue
                else:
                    print(f"[{host}:{port}]-[MSG]: REGISTERING DEVICE...{CLIENT_MSG[2:3]}")
                    connectedDevices[CLIENT_MSG[3]] = (reader, writer)
                    print(f"[{host}:{port}]-[MSG]: CONNECTED DEVICES:\r\n {connectedDevices}")
                    cmd: bytearray = bytearray(
                            b'\x00' +
                            MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD +
                            CLIENT_MSG[3:4] +
                            SERVER_SUB_COMMAND.REG_W_SERVER +
                            PERIPHERAL_EVENT.EXT_SRV_CONNECTED
                            )
                    cmd = bytearray(
                            bytearray((len(cmd) + 1).to_bytes(1, byteorder='little', signed=False)) +
                            cmd
                            )
                    
                    ret_msg: EXT_SERVER_NOTIFICATION = EXT_SERVER_NOTIFICATION(cmd)
                    connectedDevices[CLIENT_MSG[3:4]][1].write(ret_msg.COMMAND[0].to_bytes(1, 'little', signed=False))
                    await connectedDevices[CLIENT_MSG[3:4]][1].drain()
                    connectedDevices[CLIENT_MSG[3:4]][1].write(ret_msg.COMMAND)
                    await connectedDevices[CLIENT_MSG[3:4]][1].drain()
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] REGISTERED WITH SERVER...")
            else:
                print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}]: CONNECTION FOUND IN DICTIONARY...")
                print(f"RECEIVED {CLIENT_MSG.hex()!r} FROM {conn_info!r}")
                
                if CLIENT_MSG[4] == int(SERVER_SUB_COMMAND.DISCONNECT_F_SERVER.hex(), 16):
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] DISCONNECTING...")
                    connectedDevices.pop(CLIENT_MSG[3:4])
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] DISCONNECTED FROM SERVER...")
                    print(f"connected Devices: {connectedDevices}")
                    continue
                elif CLIENT_MSG[4] == int(SERVER_SUB_COMMAND.REG_W_SERVER.hex(), 16):
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] ALREADY CONNECTED TO SERVER... IGNORING...")
                    connectedDevices.pop(CLIENT_MSG[3:4])
                    continue
                else:
                    # elif CLIENT_MSG[4] in ({v: k for k, v in HUB_SUB_COMMAND.__dataclass_fields__.items()}.keys()):
                    print(f"[{host}:{port}]-[MSG]: SENDING [{CLIENT_MSG.hex()}]:[{CLIENT_MSG[3:4]!r}] FROM {conn_info!r}")
                    if os.name == 'posix':
                        Future_BTLEDevice.writeCharacteristic(handle, CLIENT_MSG, True)
        except ConnectionResetError:
            print(f"[{host}:{port}]-[MSG]: CLIENT [{conn_info[0]}:{conn_info[1]}] RESET CONNECTION... DISCONNECTED...")
            await asyncio.sleep(.05)
            connectedDevices.clear()
            return False
        except ConnectionAbortedError:
            print(
                f"[{host}:{port}]-[MSG]: CLIENT [{conn_info[0]}:{conn_info[1]}] ABORTED CONNECTION... DISCONNECTED...")
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
            # event_loop.call_soon(Future_BTLEDevice.writeCharacteristic, 0x0f, b'\x01\x00', True)
        
        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(server.serve_forever()),), timeout=.1))
        loop.run_forever()
    except NameError:
        pass
    finally:
        loop.stop()
        Future_BTLEDevice.disconnect() if os.name == 'posix' else None
        loop.close()
