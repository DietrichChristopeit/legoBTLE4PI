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
from asyncio import Event, StreamReader, StreamWriter

from tabulate import tabulate

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.messages.downstream import (DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (UpStreamMessageBuilder)
from LegoBTLE.LegoWP.types import ALL_DONE, ALL_PENDING, MESSAGE_TYPE, ECMD
from LegoBTLE.networking.experiment import Experiment

connection_status = {
        'device_name': {
                'sokt': -1,
                'hub_port': 1,
                'device_type': 'LALLES',
                'last_cmd': 'LALLESCMD',
                'last_error': 'LALLESERROR',
                'state': 'disconnected',
                'connection_attpts': 0
                }
        }

pdtabulate = lambda df: tabulate(df, headers='keys', tablefmt='psql')


class CMD_Client:
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        self._host = host
        self._port = port
        self._connected_devices: dict = {
                bytes: (Device, StreamReader, StreamWriter)
                }
        self._proceed: Event = Event()
        self._proceed.set()
        self._ext_srv_connected: Event = Event()
        self._ext_srv_connected.clear()
        self._ext_srv_listening: Event = Event()
        self._ext_srv_listening.clear()
        return
    
    async def DEV_CONNECT_SRV(self, device: Device, wait: bool = False) -> bool:
        await self._proceed.wait()
        if wait:
            self._proceed.clear()
        conn = dict()
        try:
            # device.ext_srv_notification = None
            device.ext_srv_connected.clear()
            device.ext_srv_disconnected.set()
            print(
                    f"[CLIENT]-[MSG]: ATTEMPTING TO REGISTER [{device.name}:{device.port.hex()}] WITH SERVER "
                    f"[{self._host}:"
                    f"{self._port}]...")
            reader, writer = await asyncio.open_connection(host=self._host, port=self._port)
            socket = writer.get_extra_info('socket')
            conn: dict = {device.port: (device, reader, writer)}
            
            REQUEST_MESSAGE = await device.EXT_SRV_CONNECT_REQ()
            conn[device.port][2].write(REQUEST_MESSAGE.COMMAND[:2])
            await conn[device.port][2].drain()
            conn[device.port][2].write(REQUEST_MESSAGE.COMMAND[1:])
            await conn[device.port][2].drain()  # CONN_REQU sent
            bytesToRead: bytes = await conn[device.port][1].readexactly(1)  # waiting for answer from Server
            data = bytearray(await conn[device.port][1].readexactly(int(bytesToRead.hex(), 16)))
            
            RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
            try:
                if data[2] == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
                    device.ext_srv_notification = RETURN_MESSAGE
                else:
                    self._proceed.set()
                    device.ext_srv_connected.clear()
                    device.ext_srv_disconnected.set()
                    raise TypeError(f"[DEV_CONNECT_SRV]-[MSG]: WRONG REPLY: [{data[2]}]... SOMETHING IS WRONG")
            except TypeError as E_TYPE:
                device.ext_srv_connected.clear()
                device.ext_srv_disconnected.set()
                device.ext_srv_notification = None
                self._proceed.set()
                raise TypeError from E_TYPE
        except ConnectionError as E_CON:
            conn.clear()
            device.ext_srv_connected.clear()
            print(f"CAN'T ESTABLISH CONNECTION TO SERVER...")
            self._proceed.set()
            raise ConnectionError() from E_CON
        else:
            # check if works, superfluous
            await conn[device.port][0].ext_srv_connected.wait()
            self._connected_devices[device.port] = conn[device.port]
            print(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: CONNECTION ESTABLISHED...")
            print(f"[{conn[device.port][0].name}:"
                  f"{conn[device.port][0].port.hex()}]-[{RETURN_MESSAGE.m_cmd_code_str}]: ["
                  f"{RETURN_MESSAGE.m_event_str!s}]")
            self._proceed.set()
            device.ext_srv_connected.set()
            device.ext_srv_disconnected.clear()
            self._ext_srv_connected.set()
            return self._ext_srv_connected.is_set()
    
    async def DEV_DISCONNECT_SRV(self, device: Device, wait: bool = False) -> bool:
        await self._proceed.wait()
        if wait:
            self._proceed.clear()
        DISCONNECT_MSG: DOWNSTREAM_MESSAGE = await device.EXT_SRV_DISCONNECT_REQ()
        
        self._connected_devices[device.port][2].write(DISCONNECT_MSG.COMMAND[:2])
        await self._connected_devices[device.port][2].drain()
        self._connected_devices[device.port][2].write(DISCONNECT_MSG.COMMAND[1:])
        await self._connected_devices[device.port][2].drain()
        await self._connected_devices[device.port][2].close()
        self._connected_devices.pop(device.port)
        device.ext_srv_connected.clear()
        device.ext_srv_disconnected.set()
        self._ext_srv_connected.clear()
        self._proceed.set()
        return not self._ext_srv_connected.is_set()
    
    async def CMD_SND(self, lego_cmd: DOWNSTREAM_MESSAGE, *args, **kwargs) -> bool:
        sent: Event = Event()
        sent.clear()
        try:
            port = lego_cmd.port
            # or getattr(self, 'big_object')
        except AttributeError:
            port = b'\xfe'
        
        sndCMD = lego_cmd
        print('', end="WAITING FOR SERVER CONNECTION...")
        try:
            await self._connected_devices[port][0].ext_srv_connected.wait()
            print(f"SENDING COMMAND TO SERVER: {sndCMD.COMMAND.hex()}")
            print(self._connected_devices[port][2].get_extra_info('peername'))
            self._connected_devices[port][2].write(sndCMD.COMMAND[:2])
            self._connected_devices[port][2].write(sndCMD.COMMAND[1:])
            await self._connected_devices[port][2].drain()
            sent.set()
        except (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, ConnectionError):
            print(f"[CMD_CLIENT]-[MSG]: SENDING COMMAND [{sndCMD.COMMAND.hex()}] FAILED ")
            sent.clear()
        finally:
            return sent.is_set()
    
    async def DEV_LISTEN_SRV(self, device: Device,
                             host: str = '127.0.0.1',
                             port: int = 8888,
                             wait: bool = False) -> bool:
        self._ext_srv_listening.clear()
        con_attempts = max_attempts = 10
        data: bytearray
        bytes_read: int = 0
        # main loop:
        # method can also be called for arbitrary devices directly, so we need to check if device is already connected
        
        if device.port not in self._connected_devices.keys():  # FIRST STAGE, HANDSHAKE
            while con_attempts > 0:
                con_attempts -= 1
                try:
                    inits = {asyncio.ensure_future(self.DEV_CONNECT_SRV(device=device, wait=wait))}
                    result = asyncio.gather(*inits)
                    for r in result:
                        await asyncio.wait_for(r[0], timeout=5.0)
                except (TimeoutError, ConnectionError) as e:
                    if isinstance(e, TimeoutError):
                        print(f"CONNECTION TIMED OUT: {e.args}...")
                        print(f"[CONNECT_LISTEN_SRV]-[MSG]: TIMEOUT ERROR DURING CONNECTION ATTEMPT... RETRYING "
                              f"{con_attempts}/{max_attempts}...")
                    if isinstance(e, ConnectionError):
                        print(f"CONNECTION: {e.args}...")
                        print(f"[CONNECT_LISTEN_SRV]-[MSG]: CONNECTION ERROR DURING CONNECTION ATTEMPT... RETRYING "
                              f"{con_attempts}/{max_attempts}...")
                    continue
                else:
                    print(f"[CONNECT_LISTEN_SRV]-[MSG]: DEVICE SUCCESSFULLY CONNECTED...")
                    break
            if (con_attempts - 1) < 0:
                raise SystemError(f"[CONNECT_LISTEN_SRV]-[MSG]: TOO MANY CONNECTION ATTEMPTS... GIVING UP...")
        # actual listen for sequence
        print(f"[{device.name}:{device.port.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
        while self._ext_srv_connected.is_set():
            self._ext_srv_listening.set()
            try:
                future_listening_srv = asyncio.ensure_future(
                        await self._connected_devices[device.port][1].readexactly(n=1))
                await asyncio.wait_for(future_listening_srv, timeout=5.0)
                
                bytesToRead: bytes = future_listening_srv.result()
                print(f"[{device.name}:{device.port.hex()}]-[MSG]: READING "
                      f"{int.from_bytes(bytesToRead, byteorder='little', signed=False)} BYTES")
                data = await self._connected_devices[device.port][1].readexactly(n=int(bytesToRead.hex(), 16))
                
                RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
                if RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_PORT_VALUE:
                    device.port_value = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK:
                    device.cmd_feedback_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR:
                    device.generic_error_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_PORT_NOTIFICATION:
                    device.port_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD:
                    device.ext_srv_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_HUB_ATTACHED_IO:
                    device.hub_attached_io_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ACTION:
                    device.hub_action_notification = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_DNS_HUB_ALERT:
                    device.hub_alert_notification = RETURN_MESSAGE
                else:
                    raise TypeError
            
            except TimeoutError as e:
                print(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: TIMEOUT... again...")
                if con_attempts == 0:
                    self._ext_srv_connected.clear()
                    device.ext_srv_connected.clear()
                    device.ext_srv_disconnected.set()
                    raise ConnectionError(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: "
                                          f"TOO MUCH FAILED CONNECTION ATTEMPTS... SOMETHING IS WRONG... "
                                          f"CHECK CONNECTIONS...") from e
                continue
            except (KeyError, KeyboardInterrupt) as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.port] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            except (ConnectionError, ConnectionResetError, ConnectionRefusedError) as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.port] = {b'', (None, (None, None))}
                if con_attempts == 0:
                    raise
                else:
                    print(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {con_attempts}/{max_attempts}...")
                    continue
            except Exception as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.port] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.name!s}:{device.port.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            else:
                print(f"[{device.name!s}:{device.port.hex()!s}]-"
                      f"[{RETURN_MESSAGE.m_cmd_feedback_str!s}]: "
                      f"RECEIVED [DATA] = [{RETURN_MESSAGE.COMMAND!s}]")
                continue
        self._ext_srv_listening.clear()
        return self._ext_srv_listening.is_set()


async def main():
    loop = asyncio.get_event_loop()
    EXPERIMENT_0 = Experiment()
    cmd_client: CMD_Client = CMD_Client()
    
    # creating the devices
    HUB = Hub(name="THE LEGO HUB 2.0")
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67)
    STR = SingleMotor(name="STR", port=b'\x02')
    FWD_RWD = SynchronizedMotor(name="FWD_RWD", motor_a=FWD, motor_b=RWD)
    
    # First CMD SEQUENCE: Connect the Devices to the Server using the CMD_Client
    
    CONNECTION_SEQ = [ECMD(name='con_hub', cmd=cmd_client.DEV_CONNECT_SRV, kwargs={'device': HUB}),
                      ECMD(name='con_FWD', cmd=cmd_client.DEV_CONNECT_SRV, kwargs={'device': FWD}),
                      ECMD(name='con_RWD', cmd=cmd_client.DEV_CONNECT_SRV, kwargs={'device': RWD}),
                      ECMD(name='con_STR', cmd=cmd_client.DEV_CONNECT_SRV, kwargs={'device': STR})
                      ]
    
    EXPERIMENT_0.cmd_sequence = CONNECTION_SEQ
    print(CONNECTION_SEQ)
    expectation, done, pending, as_completed = await EXPERIMENT_0.run(cmd_sequence=CONNECTION_SEQ)
    
    # Second CMD SEQUENCE: Make the Client listen to Device Commands to send to the Server
    CONNECTION_LISTEN_SEQ = [
            ECMD(name='con_hub', cmd=cmd_client.DEV_LISTEN_SRV, kwargs={'device': HUB}),
            ECMD(name='con_FWD', cmd=cmd_client.DEV_LISTEN_SRV, kwargs={'device': FWD}),
            ECMD(name='con_RWD', cmd=cmd_client.DEV_LISTEN_SRV, kwargs={'device': RWD}),
            ECMD(name='con_STR', cmd=cmd_client.DEV_LISTEN_SRV, kwargs={'device': STR})
            ]
    
    EXPERIMENT_0.cmd_sequence = CONNECTION_LISTEN_SEQ
    print(CONNECTION_LISTEN_SEQ)
    try:
        expectation, tasks_done, tasks_pending, as_completed = await EXPERIMENT_0.run(
                cmd_sequence=CONNECTION_LISTEN_SEQ,
                expect=ALL_PENDING,
                promise_max_wait=0.3
                )
    except UserWarning as uw:
        raise UserWarning("The specified Expection was not met...", uw.args) from uw
    else:
        print("EXPECTATION MET")
    print(f"{FWD.port_value}")
    # Third CMD SEQUENCE: Send Device Commands to send to the Server
    CMD_SEQ = [
            ECMD(name='con_hub', cmd=cmd_client.CMD_SND, kwargs={'lego_cmd': await HUB.GENERAL_NOTIFICATION_REQUEST()}),
            ECMD(name='con_FWD', cmd=cmd_client.CMD_SND, kwargs=({'lego_cmd': await FWD.REQ_PORT_NOTIFICATION(wait=False)})),
            ECMD(name='FWD_VAL', cmd=FWD.port_value),
            # ECMD(name='con_RWD', lego_cmd=clientbroker.DEV_LISTEN_SRV, kwargs=({'device': RWD, 'wait': True})),
            # ECMD(name='con_STR', lego_cmd=clientbroker.DEV_LISTEN_SRV, kwargs=({'device': STR, 'wait': False}))
            ]
    try:
        expectation, tasks_done, tasks_pending, as_completed = await EXPERIMENT_0.run(
                cmd_sequence=CMD_SEQ,
                expect=ALL_DONE,
                promise_max_wait=0.3,
                as_completed=False
                )
        # for c in as_completed:
        #     print(await c)
            
    except UserWarning as uw:
        raise UserWarning("The specified Expection was not met...", uw.args) from uw
    else:
        print("EXPECTATION MET")
    print(f"{FWD.port_value}")
    return


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    asyncio.run(main())
    loop.run_forever()
