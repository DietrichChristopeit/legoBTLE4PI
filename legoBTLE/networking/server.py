# coding=utf-8
"""
    legoBTLE.networking.server
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This package holds the classes to set up a server where devices can register
    and route message from and to the bluetooth sender/receiver.
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see :ref:`AUTHORS`.
    :license: MIT, see :ref:`LICENSE` for details
"""

import asyncio
import os
from asyncio import AbstractEventLoop
from asyncio.streams import IncompleteReadError
from asyncio.streams import StreamReader
from asyncio.streams import StreamWriter
from collections import defaultdict
from datetime import datetime

from legoBTLE.exceptions.Exceptions import ServerClientRegisterError, LegoBTLENoHubToConnectError, ExperimentException
from legoBTLE.legoWP.message.downstream import CMD_COMMON_MESSAGE_HEADER
from legoBTLE.legoWP.message.upstream import EXT_SERVER_NOTIFICATION
from legoBTLE.legoWP.message.upstream import UpStreamMessageBuilder
from legoBTLE.legoWP.types import MESSAGE_TYPE
from legoBTLE.legoWP.types import PERIPHERAL_EVENT
from legoBTLE.legoWP.types import SERVER_SUB_COMMAND
from legoBTLE.legoWP.types import C

if os.name == 'posix':
    from bluepy import btle
    from bluepy.btle import BTLEInternalError, Peripheral

global host
global port
if os.name == 'posix':
    global Future_BTLEDevice

connectedDevices: defaultdict = defaultdict()
internalDevices: defaultdict = defaultdict()

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
            """Distribute received notifications to the respective device.

            Parameters
            ----------
            cHandle :
                Handle of the data
            data : bytearray
                Notifications from the bluetooth device as bytearray.
                
            Returns
            -------
            None
                Nothing
            """
            print(f"[BTLEDelegate]-[MSG]: Returned NOTIFICATION = {data.hex()}")
            M_RET = UpStreamMessageBuilder(data, debug=True).build()
            
            try:
                if (M_RET is not None) and (M_RET.m_header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO) and (M_RET.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED):
                    print(f"{C.BOLD}{C.FAIL}RAW:\tCOMMAND         -->  {M_RET.COMMAND}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tHEADER          -->  {M_RET.m_header}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_TYPE          -->  {M_RET.m_header.m_type}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_TYPE ==       -->  {M_RET.m_header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_IO_EVENT      -->  {M_RET.m_io_event}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_IO_EVENT ==   -->  {M_RET.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_PORT          -->  {M_RET.m_port}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_PORT_A        -->  {M_RET.m_port_a}{C.ENDC}", end="\r\n")
                    print(f"{C.BOLD}{C.FAIL}RAW:\tM_PORT_B        -->  {M_RET.m_port_b}{C.ENDC}", end="\r\n")
                if (M_RET is not None) and (M_RET.m_header.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO) and (
                        M_RET.m_io_event == PERIPHERAL_EVENT.VIRTUAL_IO_ATTACHED):
                    # we search for the setup port with which the combined device first registered
                    setup_port: int = (110 +
                                       1 * int.from_bytes(M_RET.m_port_a, 'little', signed=False) +
                                       2 * int.from_bytes(M_RET.m_port_b, 'little', signed=False)
                                       )
                    print(f"*****************************************************SETUPPORT: {setup_port}")
                    connectedDevices[setup_port][1].write(data[0:1])
                    asyncio.create_task(connectedDevices[setup_port][1].drain())
                    connectedDevices[setup_port][1].write(data)
                    asyncio.create_task(connectedDevices[setup_port][1].drain())
                    
                    # change initial port value of motor_a.port + motor_b.port to virtual port
                    connectedDevices[data[3]] = connectedDevices[setup_port][0], connectedDevices[setup_port][1]
                    del connectedDevices[setup_port]
                elif (M_RET.m_header.m_type == MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR) and (M_RET.m_error_cmd == MESSAGE_TYPE.DNS_VIRTUAL_PORT_SETUP):
                    print("*" * 10, f"[BTLEDelegate.handleNotification()]-[MSG]:  {C.BOLD}{C.OKBLUE}VIRTUAL PORT SETUP: ACK -- BEGIN\r\n")
                    print("*" * 10,
                          f"[BTLEDelegate.handleNotification()]-[MSG]:  {C.BOLD}{C.OKBLUE}RECEIVED GENERIC_ERROR_NOTIFICATION: OK, see\r\n")
                    print("*" * 10,
                          f"[BTLEDelegate.handleNotification()]-[MSG]:  {C.BOLD}{C.OKBLUE}https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#hub-attached-i-o\r\n")
                    print("*" * 10,
                          f"[BTLEDelegate.handleNotification()]-[MSG]:  {C.BOLD}{C.OKBLUE}VIRTUAL PORT SETUP: ACK -- END \r\n")
                else:
                    print(f"To PORT: {data[3]}")
                    connectedDevices[data[3]][1].write(data[0:1])
                    connectedDevices[data[3]][1].write(data)
                    asyncio.create_task(connectedDevices[data[3]][1].drain())
            except TypeError as te:
                print(
                        f"[BTLEDelegate]-[MSG]: WRONG ANSWER\r\n\t\t{data.hex()}\r\nFROM BTLE... {C.FAIL}IGNORING...{C.ENDC}\r\n\t{te.args}")
                return
            except KeyError as ke:
                print(f"[BTLEDelegate]-[MSG]: DEVICE CLIENT AT PORT [{data[3]}] {C.BOLD}{C.WARNING}NOT CONNECTED{C.ENDC} "
                      f"TO SERVER [{self._remoteHost[0]}:{self._remoteHost[1]}]... {C.WARNING}Ignoring Notification from BTLE...{C.ENDC}")
            else:
                print(f"[BTLEDelegate]-[MSG]: {C.BOLD}{C.OKBLUE}FOUND PORT {data[3]} / {C.UNDERLINE}MESSAGE SENT...{C.ENDC}\n-----------------------")
            return
    
    
    async def connectBTLE(loop: AbstractEventLoop, deviceaddr: str = '90:84:2B:5E:CF:1F', host: str = '127.0.0.1',
                          btleport: int = 9999) -> Peripheral:
        """.. import:: <isonum.txt>
        Establish the LEGO\ |copy| Hub <-> Computer bluetooth connection.

        Parameters
        ----------
        loop : `AbstractEventLoop`
            A reference to the event lopp.
        btleport : int
            The server port.
        host : str
            The hostname.
        deviceaddr : str
            The MAC Address of the LEGO\ |copy| Hub.
        
        Raises
        ------
        Exception
        
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
            loop.call_later(.0015, _listenBTLE, btledevice, loop, debug)
        return


async def _listen_clients(reader: StreamReader, writer: StreamWriter, debug: bool = True) -> bool:
    """This is the central message receiving function.
    
    The function listens for incoming message (the commands) from the devices.
    Once a message has been received it is - if not the initial connection request - sent to the BTLE device.
    
    Parameters
    ----------
    reader : StreamReader
        The reader instance
    writer : StreamWriter
        The write instance.
    debug : bool
        If ``True``:
            Verbose Messages to stdout
        else:
            don't show.

    Returns
    -------
    bool
        ``True`` if everything is good, ``False`` otherwise.
        
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
            CLIENT_MSG_DATA: bytearray = bytearray(await reader.readexactly(n=size))
            
            if CLIENT_MSG_DATA[2] == MESSAGE_TYPE.UPS_DNS_GENERAL_HUB_NOTIFICATIONS[0]:
                print(f"{C.BOLD}{C.FAIL}{CLIENT_MSG_DATA.hex()}{C.ENDC}")
                if debug:
                    print(
                            f"[{host}:{port}]-[MSG]: {C.BOLD}{C.UNDERLINE}{C.OKBLUE}SENDING{C.ENDC}: "
                            f"{C.OKGREEN}{C.BOLD}{handle}, {CLIENT_MSG_DATA[2:].hex()}{C.ENDC} {C.BOLD}{C.UNDERLINE}{C.OKBLUE} "
                            f"FROM{C.ENDC}{C.BOLD}{C.OKBLUE} DEVICE [{conn_info[0]}:{conn_info[1]}]{C.UNDERLINE} "
                            f"TO{C.ENDC}{C.BOLD}{C.OKBLUE} BTLE device{C.ENDC}")
                if os.name == 'posix':
                    print(f"HANDLE: {handle} / DATA: {CLIENT_MSG_DATA[2:]}")
                    Future_BTLEDevice.writeCharacteristic(0x0f, val=CLIENT_MSG_DATA[2:], withResponse=True)
                continue
            if debug:
                print(
                        f"[{host}:{port}]-[MSG]: {C.BOLD}{C.OKBLUE}{C.UNDERLINE}RECEIVED "
                        f"CLIENTMESSAGE{C.ENDC}{C.BOLD}{C.OKBLUE}: {CLIENT_MSG_DATA.hex()} FROM DEVICE "
                        f"[{conn_info[0]}:{conn_info[1]}]{C.ENDC}")
                
            con_key_index = CLIENT_MSG_DATA[3]
            
            if con_key_index not in connectedDevices.keys():
                # wait until Connection Request from client
                if ((CLIENT_MSG_DATA[2] != MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[0])
                        or (CLIENT_MSG_DATA[-1] != SERVER_SUB_COMMAND.REG_W_SERVER[0])):
                    continue
                else:
                    if ((CLIENT_MSG_DATA[2] == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[0])
                            or (CLIENT_MSG_DATA[-1] == SERVER_SUB_COMMAND.REG_W_SERVER[0])):
                        if debug:
                            print("*"*10, f" {C.BOLD}{C.OKBLUE}NEW DEVICE: {con_key_index} DETECTED", end="*" * 10+f"{C.ENDC}\r\n")
                        connectedDevices[con_key_index] = (reader, writer)
                        if debug:
                            print("**", " " * 8, f"\t\t{C.BOLD}{C.OKBLUE}DEVICE: {con_key_index} REGISTERED",
                                  end="*" * 10 + f"{C.ENDC}\r\n")
                            print(f"{C.BOLD}{C.OKBLUE}*"*20, end=f"{C.ENDC}\r\n")
    
                            print("*" * 10, f" {C.BOLD}{C.OKBLUE}[{host}:{port}]-[MSG]: SUMMARY CONNECTED DEVICES:{C.ENDC}")
                            for con_dev_k, con_dev_v in connectedDevices.items():
                                print(f"{C.BOLD}{C.OKBLUE}**[{host}:{port}]-[MSG]: \t"
                                      f"PORT: {con_dev_k} / DEVICE: {con_dev_v[1]}{C.ENDC}")
                            print(f"{C.BOLD}{C.OKBLUE}*" * 20, end=f"{C.ENDC}\r\n")
                        
                        ACK_MSG_DATA: bytearray = CLIENT_MSG_DATA
                        ACK_MSG_DATA[-1:] = PERIPHERAL_EVENT.EXT_SRV_CONNECTED
                        ACK_MSG = UpStreamMessageBuilder(data=ACK_MSG_DATA, debug=True).build()
                        
                        connectedDevices[con_key_index][1].write(ACK_MSG.COMMAND[0:1])
                        await connectedDevices[con_key_index][1].drain()
                        connectedDevices[con_key_index][1].write(ACK_MSG.COMMAND)
                        await connectedDevices[con_key_index][1].drain()
                        if debug:
                            print(f"[{host}:{port}]-[MSG]: SENT ACKNOWLEDGEMENT TO DEVICE AT [{conn_info[0]}:{conn_info[1]}]...")
                    else:
                        print("*" * 10, f" {C.BOLD}{C.FAIL}WRONG COMMAND / THIS SHOULD NOT BE POSSIBLE",
                                  end="*" * 10 + f"{C.ENDC}\r\n")
                        raise ServerClientRegisterError(message=CLIENT_MSG_DATA.hex())
            else:
                if debug:
                    print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}]: CONNECTION FOUND IN DICTIONARY...")
                    print(
                            f"[{host}:{port}]-[MSG]: RECEIVED [{CLIENT_MSG_DATA.hex()!r}] FROM "
                            f"[{conn_info[0]}:{conn_info[1]}]")
                
                if ((CLIENT_MSG_DATA[2] == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD[0])
                        and (CLIENT_MSG_DATA[-1] == SERVER_SUB_COMMAND.DISCONNECT_F_SERVER[0])):
                    print(
                            f"[{host}:{port}]-[MSG]: RECEIVED REQ FOR DISCONNECTING DEVICE: "
                            f"[{conn_info[0]}:{conn_info[1]}]...")
                    disconnect: bytearray = bytearray(
                            b'\x00' +
                            MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD +
                            CLIENT_MSG_DATA[3:4] +
                            SERVER_SUB_COMMAND.DISCONNECT_F_SERVER +
                            PERIPHERAL_EVENT.EXT_SRV_DISCONNECTED
                            )
                    disconnect = bytearray(
                            bytearray((len(disconnect) + 1).to_bytes(1, byteorder='little', signed=False)) +
                            disconnect
                            )
                    ACK: EXT_SERVER_NOTIFICATION = EXT_SERVER_NOTIFICATION(disconnect)
                    connectedDevices[con_key_index][1].write(ACK.m_header.m_length)
                    await connectedDevices[con_key_index][1].drain()
                    connectedDevices[con_key_index][1].write(ACK.COMMAND)
                    await connectedDevices[con_key_index][1].drain()
                    connectedDevices.pop(con_key_index)
                    if debug:
                        print(f"[{host}:{port}]-[MSG]: DEVICE [{conn_info[0]}:{conn_info[1]}] DISCONNECTED FROM SERVER...")
                        print(f"connected Devices: {connectedDevices}")
                    continue
                elif CLIENT_MSG_DATA[2] == MESSAGE_TYPE.DNS_VIRTUAL_PORT_SETUP[0]:
                    if debug:
                        print(f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] RECEIVED VIRTUAL PORT SETUP REQUEST...")
                elif ((CLIENT_MSG_DATA[2] == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD)
                      and (CLIENT_MSG_DATA[4] == SERVER_SUB_COMMAND.REG_W_SERVER)):
                    if debug:
                        print(
                            f"[{host}:{port}]-[MSG]: [{conn_info[0]}:{conn_info[1]}] ALREADY CONNECTED, IGNORING REQUEST...")
                    continue
                else:
                    if debug:
                        print(f"[{host}:{port}]-[MSG]: SENDING [{CLIENT_MSG_DATA.hex()}]:[{con_key_index!r}] "
                              f"FROM {conn_info!r}")
                if os.name == 'posix':
                    Future_BTLEDevice.writeCharacteristic(0x0e, CLIENT_MSG_DATA, True)
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
