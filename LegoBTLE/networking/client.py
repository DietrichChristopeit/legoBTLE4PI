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
from collections import namedtuple

from tabulate import tabulate

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.messages.downstream import (DOWNSTREAM_MESSAGE)
from LegoBTLE.LegoWP.messages.upstream import (UpStreamMessageBuilder)
from LegoBTLE.LegoWP.types import MESSAGE_TYPE, MOVEMENT
from LegoBTLE.networking.running import CMD_SPlayer

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
        self._connected_devices: {
                bytes: [Device, [StreamReader, StreamWriter]]
                } = {}
        return
    
    async def DEV_CONNECT_SRV(self, device: Device, *args, **kwargs) -> Event:
        
        conn = {
                bytes: [Device, [StreamReader, StreamWriter]]
                }
        try:
            device.ext_srv_notification = None
            device.ext_srv_connected.clear()
            print(
                    f"[CLIENT]-[MSG]: ATTEMPTING TO REGISTER [{device.DEV_NAME}:{device.DEV_PORT.hex()}] WITH SERVER "
                    f"[{self._host}:"
                    f"{self._port}]...")
            conn = {
                    device.DEV_PORT: (device, await asyncio.open_connection(host=self._host, port=self._port))
                    }
            
            REQUEST_MESSAGE = conn[device.DEV_PORT][0].EXT_SRV_CONNECT_REQ()
            conn[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[:2])
            await conn[device.DEV_PORT][1][1].drain()
            conn[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[1:])
            await conn[device.DEV_PORT][1][1].drain()  # CONN_REQU sent
            bytesToRead: bytes = await conn[device.DEV_PORT][1][0].readexactly(1)  # waiting for answer from Server
            data = bytearray(await conn[device.DEV_PORT][1][0].readexactly(int(bytesToRead.hex(), 16)))
            
            RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
            try:
                if data[2] == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
                    device.ext_srv_notification = RETURN_MESSAGE
                else:
                    raise TypeError(f"[DEV_CONNECT_SRV]-[MSG]: WRONG REPLY: [{data[2]}]... SOMETHING IS WRONG")
            except TypeError as E_TYPE:
                device.ext_srv_connected.clear()
                device.ext_srv_notification = None
                raise from E_TYPE
        except ConnectionError as E_CON:
            conn.clear()
            device.ext_srv_connected.clear()
            print(f"CAN'T ESTABLISH CONNECTION TO SERVER...{e.c_args}")
            raise ConnectionError(e.c_args) from E_CON
        else:
            # check if works, superfluous
            await conn[device.DEV_PORT][0].ext_srv_connected.wait()
            self._connected_devices[device.DEV_PORT] = conn[device.DEV_PORT]
            print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION ESTABLISHED...")
            print(f"[{conn[device.DEV_PORT][0].DEV_NAME}:"
                  f"{conn[device.DEV_PORT][0].DEV_PORT.hex()}]-[{RETURN_MESSAGE.m_cmd_code_str}]: ["
                  f"{RETURN_MESSAGE.m_event_str!s}]")
            return device.ext_srv_connected
    
    async def DEV_DISCONNECT_SRV(self, device: Device, *args, **kwargs) -> Event:
        DISCONNECT_MSG: DOWNSTREAM_MESSAGE = device.EXT_SRV_DISCONNECT_REQ()
        
        self._connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND[:2])
        await self._connected_devices[device.DEV_PORT][1][1].drain()
        self._connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND[1:])
        await self._connected_devices[device.DEV_PORT][1][1].drain()
        await self._connected_devices[device.DEV_PORT][1][1].close()
        self._connected_devices.pop(device.DEV_PORT)
        device.ext_srv_connected.clear()
        device.ext_srv_disconnected.set()
        return self._connected_devices[device.DEV_PORT][0].ext_srv_disconnected
    
    async def CMD_SND(self, cmd: DOWNSTREAM_MESSAGE, *args, **kwargs) -> Event:
        sent: Event = Event()
        sent.set()
        
        DEV_PORT = cmd.port
        
        sndCMD = cmd
        print('', end="WAITING FOR SERVER CONNECTION...")
        try:
            await self._connected_devices[DEV_PORT][0].ext_srv_connected.wait()
            print(f"SENDING COMMAND TO SERVER: {sndCMD.COMMAND.hex()}")
            print(self._connected_devices[DEV_PORT][1][1].get_extra_info('peername'))
            self._connected_devices[DEV_PORT][1][1].write(sndCMD.COMMAND[:2])
            self._connected_devices[DEV_PORT][1][1].write(sndCMD.COMMAND[1:])
            await self._connected_devices[DEV_PORT][1][1].drain()
        except (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, ConnectionError):
            print(f"[CMD_CLIENT]-[MSG]: SENDING COMMAND [{sndCMD.COMMAND.hex()}] FAILED ")
            sent.clear()
        finally:
            return sent
    
    async def DEV_LISTEN_SRV(self, device: Device,
                             host: str = '127.0.0.1',
                             port: int = 8888,
                             *args,
                             **kwargs) -> bool:
        
        con_attempts = max_attempts = 10
        data: bytearray
        bytes_read: int = 0
        # main loop:
        # method can also be called for arbitrary devices directly, so we need to check if device is already connected
        
        if device.DEV_PORT not in self._connected_devices.keys():  # FIRST STAGE, HANDSHAKE
            while con_attempts > 0:
                con_attempts -= 1
                try:
                    inits = {asyncio.ensure_future(self.DEV_CONNECT_SRV(device=device))}
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
        while True:
            print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
            try:
                future_listening_srv = asyncio.ensure_future(
                        await self._connected_devices[device.DEV_PORT][1][0].exactly(n=1))
                await asyncio.wait_for(future_listening_srv, timeout=5.0)
                
                bytesToRead: bytes = future_listening_srv.result()
                print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: READING "
                      f"{int.from_bytes(bytesToRead, byteorder='little', signed=False)} BYTES")
                data = await self._connected_devices[device.DEV_PORT][1][0].readexactly(n=int(bytesToRead.hex(), 16))
                
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
                print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: TIMEOUT... again...")
                if con_attempts == 0:
                    raise TimeoutError(print, e.args)
                continue
            except (KeyError, KeyboardInterrupt) as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            except (ConnectionError, ConnectionResetError, ConnectionRefusedError) as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                if con_attempts == 0:
                    raise
                else:
                    print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {con_attempts}/{max_attempts}...")
                    continue
            except Exception as e:
                device.ext_srv_connected.clear()
                self._connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            else:
                print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-"
                      f"[{RETURN_MESSAGE.m_cmd_feedback_str!s}]: "
                      f"RECEIVED [DATA] = [{RETURN_MESSAGE.COMMAND!s}]")
                continue
        return False


async def main():
    CMD = namedtuple('CMD', ('id', 'cmd', 'c_args', 'kwargs'))
    
    # Creating client object
    clientbroker: CMD_Client = CMD_Client()
    
    # Creating command sequence player for use with client
    CMD_SEQUENCE_PLAYER: CMD_SPlayer
    
    # creating the devices
    HUB = Hub(name="THE LEGO HUB 2.0")
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67)
    STR = SingleMotor(name="STR", port=b'\x02')
    FWD_RWD = SynchronizedMotor(name="FWD_RWD", motor_a=FWD, motor_b=RWD)
    
    # First CMD SEQUENCE: Connect the Devices to the Server using the CMD_Client
    
    CONNECTION_SEQ = [
            CMD('hub_con', clientbroker.DEV_CONNECT_SRV, {'device': HUB}, None),
            CMD('rwd_con', clientbroker.DEV_CONNECT_SRV, {'device': RWD, 'wait': True, 'result': bool}, None),
            CMD('fwd_con', clientbroker.DEV_CONNECT_SRV, {'device': FWD}, None),
            CMD('str_con', clientbroker.DEV_CONNECT_SRV, {'device': STR}, None)
            ]
    
    CMD_SEQUENCE_PLAYER = CMD_SPlayer()
    results = await CMD_SEQUENCE_PLAYER.play_sequence(cmd_sequence=CONNECTION_SEQ)
    print(f"Results:" + '\r\n' + f"{results!s}")
    
    LISTEN_SEQ = {
            CMD('hub_lstn', clientbroker.DEV_LISTEN_SRV, {'device': HUB}, None),
            CMD('fwd_lstn', clientbroker.DEV_LISTEN_SRV, {'device': FWD, 'wait': True, 'result': bool}, None),
            CMD('rwd_lstn', clientbroker.DEV_LISTEN_SRV, {'device': RWD}, None),
            CMD('str_lstn', clientbroker.CMD_SND, {'cmd': RWD.GOTO_ABS_POS(speed=50, abs_pos=900, abs_max_power=72,
                                                                               on_completion=MOVEMENT.COAST, wait=True)
                                                   },
                None),
            }
    
    await CMD_SEQUENCE_PLAYER.play_sequence(cmd_sequence=LISTEN_SEQ)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        asyncio.run(main())
        loop.run_forever()
    except (ConnectionError, TypeError, RuntimeError, Exception) as e:
        print(f'[CMD_CLIENT]-[MSG]: SERVER DOWN OR CONNECTION REFUSED... COMMENCE SHUTDOWN...')
        loop.stop()
    finally:
        loop.close()
        print(f'[CMD_CLIENT]-[MSG]: SHUTDOWN COMPLETED...')
