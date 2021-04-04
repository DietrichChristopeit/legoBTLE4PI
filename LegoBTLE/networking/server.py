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
from asyncio import AbstractEventLoop
from asyncio.streams import IncompleteReadError
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter
from collections import defaultdict
from datetime import datetime

from LegoBTLE.LegoWP.messages.upstream import EXT_SERVER_NOTIFICATION
from LegoBTLE.LegoWP.messages.upstream import UpStreamMessageBuilder
from LegoBTLE.LegoWP.types import MESSAGE_TYPE
from LegoBTLE.LegoWP.types import PERIPHERAL_EVENT
from LegoBTLE.LegoWP.types import SERVER_SUB_COMMAND
from LegoBTLE.LegoWP.types import C

if os.name == 'posix':
    from bluepy import btle
    from bluepy.btle import BTLEInternalError, Peripheral

global host
global port
if os.name == 'posix':
    global Future_BTLEDevice

connectedDevices = defaultdict()
internalDevices = defaultdict()

if os.name == 'posix':
    class BTLEDelegate(btle.DefaultDelegate):
        """Delegate class that initially handles the raw data coming from the Lego(c) Model.

        """
        def __init__(self, loop: AbstractEventLoop, remoteHost=('127.0.0.1', 8888)):
            
            super().__init__()
            self._loop = loop
            self._remoteHost = remoteHost
            return
        
        def handleNotification(self, cHandle, data):  # actual Callback function
            """

            Parameters
            ----------
            cHandle :
            data :

            Returns
            -------

            """
            print(f"[BTLEDelegate]-[MSG]: Returned NOTIFICATION = {data.hex()}")
            try:
                upsmb = UpStreamMessageBuilder(data, debug=True)
                M_RET = upsmb.build()
                lastBuildPort = upsmb.lastBuildPort
                
                
            except TypeError as te:
                print(
                    f"[BTLEDelegate]-[MSG]: Wrong answer\r\n\t\t{data.hex()}\r\nfrom BTLE... {C.FAIL}IGNORING...{C.ENDC}\r\n\t{te.args}")
                return
            try:
                port: int = -1
                if (M_RET.m_header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO) and (
                        M_RET.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED):
                        
                    port = 100 + M_RET.m_port_a + M_RET.m_port_b
                    
                    connectedDevices[port][1].write(
                            M_RET.m_header.m_length)
                    connectedDevices[port][1].write(
                            M_RET.COMMAND)
                    loop.create_task(
                            connectedDevices[port][1].drain())
                    
                    # change initial port value of motor_a.port + motor_b.port to virtual port
                    connectedDevices[lastBuildPort] = connectedDevices[port]
                    del connectedDevices[port]
                else:  # .m_header.m_length
                    connectedDevices[port][1].write(len(M_RET.COMMAND) + 1)
                    connectedDevices[port][1].write(M_RET.COMMAND)
                    loop.create_task(connectedDevices[M_RET.m_port[0]][1].drain())
            except KeyError as ke:
                print(f"[BTLEDelegate]-[MSG]: DEVICE CLIENT AT PORT [{M_RET.m_port[0]}] {C.BOLD}{C.WARNING}NOT CONNECTED{C.ENDC} "
                      f"TO SERVER [{self._remoteHost[0]}:{self._remoteHost[1]}]... {C.WARNING}Ignoring Notification from BTLE...{C.ENDC}")
            else:
                print(f"[BTLEDelegate]-[MSG]: {C.BOLD}{C.OKBLUE}FOUND PORT {M_RET.m_port[0]} / {C.UNDERLINE}MESSAGE SENT...{C.ENDC}\n-----------------------")
            return
    
    
    async def connectBTLE(loop: AbstractEventLoop, deviceaddr: str = '90:84:2B:5E:CF:1F', host: str = '127.0.0.1',
                          btleport: int = 9999) -> Peripheral:
        """Establish the Lego(c) Hub <-> Computer bluetooth connection.

        :param loop:
        :type loop:
        :param btleport: The server port.
        :type btleport: int
        :param host: The hostname.
        :type host: str
        :param deviceaddr: The MAC Address of the Lego(c) Hub.
        :type deviceaddr: str
        :raises Exception: Reraises any Exception encountered.
        
        """
        
        print(f"[BTLE]-[MSG]: {C.HEADER}{C.BLINK}COMMENCE CONNECT TO [{deviceaddr}]{C.ENDC}...")
        try:
            BTLE_DEVICE: Peripheral = Peripheral(deviceaddr)
            BTLE_DEVICE.withDelegate(BTLEDelegate(loop=loop, remoteHost=(host, 8888)))
        except Exception as btle_ex:
            raise
        else:
            print(f"[{deviceaddr}]-[MSG]: {C.OKBLUE}CONNECTION TO [{deviceaddr}] {C.BOLD}{C.UNDERLINE}COMPLETE{C.ENDC}...")
            return BTLE_DEVICE
    
    
    def _listenBTLE(btledevice: Peripheral, loop, debug: bool = False):
        try:
            if btledevice.waitForNotifications(.001):
                if debug:
                    print(f"[SERVER]-[MSG]: NOTIFICATION RECEIVED... [T: {datetime.timestamp(datetime.now())}]")
        except BTLEInternalError:
            pass
        finally:
            loop.call_later(.0013, _listenBTLE, btledevice, loop, debug)
        return


async def _listen_clients(reader: StreamReader, writer: StreamWriter, debug: bool = False) -> bool:
    """This is the central message receiving function.
    
    The function listens for incoming messages (the commands) from the devices. 
    Once a message has been received it is - if not the initial connection request - sent to the BTLE Device.
     
    
    Args:
        reader (StreamReader): The reader instance
        writer (StreamWriter): The write instance.
        debug (bool):
            If True:
                Verbose Messages to stdout
            else:
                don't show.

    Returns:
        (bool): True if everything is OK, False otherwise.
        
    """
    
    global host
    global port
    global Future_BTLEDevice
    conn_info = writer.get_extra_info('peername')
    
    size: int = 0
    handle: int = -1
    
    while True:
        try:
            carrier_info: bytearray = bytearray(await reader.readexactly(n=2))
            size: int = carrier_info[1]
            handle: int = carrier_info[0]
            print(f"[{host}:{port}]-[MSG]: {C.OKGREEN}CARRIER SIGNAL DETECTED: handle={handle}, size={size}...{C.ENDC}")
            CLIENT_MSG: bytearray = bytearray(await reader.readexactly(n=size))
            print(f"[{host}:{port}]-[MSG]: {C.OKGREEN}DATA RECEIVED: {CLIENT_MSG.hex()}...{C.ENDC}")
            
            if handle == 15:
                if debug:
                    print(
                            f"[{host}:{port}]-[MSG]: {C.BOLD, C.UNDERLINE, C.OKBLUE}SENDING{C.ENDC}: "
                            f"{C.OKGREEN, C.BOLD, handle}, {CLIENT_MSG.hex(), C.ENDC} {C.BOLD, C.UNDERLINE, C.OKBLUE} "
                            f"FROM{C.ENDC, C.BOLD, C.OKBLUE} DEVICE [{conn_info[0]}:{conn_info[1]}]{C.UNDERLINE} "
                            f"TO{C.ENDC, C.BOLD, C.OKBLUE} BTLE Device{C.ENDC}")
                if os.name == 'posix':
                    Future_BTLEDevice.writeCharacteristic(0x0f, b'\x01\x00', True)
                continue
                
            if debug:
                print(
                        f"[{host}:{port}]-[MSG]: {C.BOLD, C.OKBLUE, C.UNDERLINE}RECEIVED "
                        f"CLIENTMESSAGE{C.ENDC, C.BOLD, C.OKBLUE}: {CLIENT_MSG.hex()} FROM DEVICE "
                        f"[{conn_info[0]}:{conn_info[1]}]{C.ENDC}")
            
            con_key_index = CLIENT_MSG[3]
            
            if con_key_index not in connectedDevices.keys():
                # wait until Connection Request from client
                if (CLIENT_MSG[2] != MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[0]) \
                        or (CLIENT_MSG[-1] != SERVER_SUB_COMMAND.REG_W_SERVER[0]):
                    continue
                else:
                    print(f"[{host}:{port}]-[MSG]: REGISTERING DEVICE...{con_key_index}")
                    connectedDevices[con_key_index] = (reader, writer)
                    print(f"[{host}:{port}]-[MSG]: CONNECTED DEVICES:\r\n {connectedDevices}")
                    connect: bytearray = bytearray(
                            b'\x00' +
                            MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD +
                            CLIENT_MSG[3:4] +
                            SERVER_SUB_COMMAND.REG_W_SERVER +
                            PERIPHERAL_EVENT.EXT_SRV_CONNECTED
                            )
                    connect = bytearray(
                            bytearray((len(connect) + 1).to_bytes(1,
                                                                  byteorder='little',
                                                                  signed=False)
                                      ) +  # length 1 per Lego(c) Wireless Protocol
                            connect
                            )
                    
                    ACK: EXT_SERVER_NOTIFICATION = EXT_SERVER_NOTIFICATION(connect)
                    connectedDevices[con_key_index][1].write(ACK.COMMAND[0].to_bytes(1, 'little', signed=False))
                    await connectedDevices[con_key_index][1].drain()
                    connectedDevices[con_key_index][1].write(ACK.COMMAND)
                    await connectedDevices[con_key_index][1].drain()
                    print(f"[{host}:{port}]-[MSG]: DEVICE CLIENT [{conn_info[0]}:{conn_info[1]}] REGISTERED WITH SERVER...")
            else:
                carrier_read_done = False
                if debug:
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}]: CONNECTION FOUND IN DICTIONARY...")
                    print(
                            f"[{host}:{port}]-[MSG]: RECEIVED [{CLIENT_MSG.hex()!r}] FROM "
                            f"[{conn_info[0]}:{conn_info[1]}]")
                
                if CLIENT_MSG[-1] == SERVER_SUB_COMMAND.DISCONNECT_F_SERVER[0]:
                    print(
                            f"[{host}:{port}]-[MSG]: RECEIVED REQ FOR DISCONNECTING DEVICE: "
                            f"[{conn_info[0]}:{conn_info[1]}]...")
                    disconnect: bytearray = bytearray(
                            b'\x00' +
                            MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD +
                            CLIENT_MSG[3:-1] +
                            SERVER_SUB_COMMAND.DISCONNECT_F_SERVER +
                            PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED
                            )
                    disconnect = bytearray(
                            bytearray((len(disconnect) + 1).to_bytes(1, byteorder='little', signed=False)) +
                            disconnect
                            )
                    ACK: EXT_SERVER_NOTIFICATION = EXT_SERVER_NOTIFICATION(disconnect)
                    connectedDevices[con_key_index][1].write(ACK.COMMAND[0].to_bytes(1, 'little', signed=False))
                    await connectedDevices[con_key_index][1].drain()
                    connectedDevices[con_key_index][1].write(ACK.COMMAND)
                    await connectedDevices[con_key_index][1].drain()
                    connectedDevices.pop(con_key_index)
                    print(f"[{host}:{port}]-[MSG]: DEVICE [{conn_info[0]}:{conn_info[1]}] DISCONNECTED FROM SERVER...")
                    print(f"connected Devices: {connectedDevices}")
                    continue
                elif CLIENT_MSG[5] == SERVER_SUB_COMMAND.REG_W_SERVER[0]:
                    if debug:
                        print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] ALREADY CONNECTED TO SERVER... "
                              f"IGNORING...")
                    connectedDevices.pop(con_key_index)
                    continue
                else:
                    if debug:
                        print(f"[{host}:{port}]-[MSG]: SENDING [{CLIENT_MSG.hex()}]:[{con_key_index!r}] "
                              f"FROM {conn_info!r}")
                    if os.name == 'posix':
                        Future_BTLEDevice.writeCharacteristic(0x0e, CLIENT_MSG, True)
        except (IncompleteReadError, ConnectionError, ConnectionResetError):
            print(f"[{host}:{port}]-[MSG]: CLIENT [{conn_info[0]}:{conn_info[1]}] RESET CONNECTION... "
                  f"DISCONNECTED...")
            await asyncio.sleep(.05)
            connectedDevices.clear()
            return False
        except ConnectionAbortedError:
            print(
                    f"[{host}:{port}]-[MSG]: CLIENT [{conn_info[0]}:{conn_info[1]}] ABORTED CONNECTION... "
                    f"DISCONNECTED...")
            await asyncio.sleep(.05)
            connectedDevices.clear()
            return False
        continue
    return True


if __name__ == '__main__':
    
    global Future_BTLEDevice
    
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(asyncio.start_server(
            _listen_clients, '127.0.0.1', 8888))
    try:
        
        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(server.serve_forever()),), timeout=.1))
        host, port = server.sockets[0].getsockname()
        print(f"[{host}:{port}]-[MSG]: SERVER RUNNING...")
        if (os.name == 'posix') and callable(connectBTLE) and callable(_listenBTLE):
            try:
                Future_BTLEDevice = loop.run_until_complete(asyncio.ensure_future(connectBTLE(loop=loop)))
            except Exception as btle_ex:
                raise
            else:
                loop.call_soon(_listenBTLE, Future_BTLEDevice, loop)
                print(f"[{host}:{port}]: BTLE CONNECTION TO [{Future_BTLEDevice.services} SET UP...")
        
        loop.run_forever()
    except KeyboardInterrupt:
        print(f"SHUTTING DOWN...")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        
        loop.close()
