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
import contextlib
from asyncio import StreamReader, StreamWriter

from tabulate import tabulate

from LegoBTLE.CONTROL_CENTRAL.running import CMD_Sequence
from LegoBTLE.Device import ADevice
from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.messages.downstream import (CMD_EXT_SRV_CONNECT_REQ, DOWNSTREAM_MESSAGE, EXT_SRV_DISCONNECTED_SND)
from LegoBTLE.LegoWP.messages.upstream import (UpStreamMessageBuilder)
from LegoBTLE.LegoWP.types import MESSAGE_TYPE

host = '127.0.0.1'
port = 8888

connection_status = {
        'device_name': {
                'sokt':              -1,
                'hub_port':          1,
                'device_type':       'LALLES',
                'last_cmd':          'LALLESCMD',
                'last_error':        'LALLESERROR',
                'state':             'disconnected',
                'connection_attpts': 0
                }
        }

pdtabulate = lambda df: tabulate(df, headers='keys', tablefmt='psql')


async def event_wait(evt, timeout):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def DEV_CONNECT_SRV(connected_devices: {
        bytes: [Device, [StreamReader, StreamWriter]]
        },
                          device: Device,
                          host: str = '127.0.0.1',
                          port: int = 8888) -> bool:
    conn = {
            bytes: [Device, [StreamReader, StreamWriter]]
            }
    try:
        device.ext_srv_notification = None
        conn = {
                device.DEV_PORT: (device, await asyncio.open_connection(host=host, port=port))
                }
        REQUEST_MESSAGE = CMD_EXT_SRV_CONNECT_REQ(port=device.DEV_PORT)
        # print(f"SENDING REQ to SERVER: {REQUEST_MESSAGE.COMMAND.hex()}")
        # print(f"SENDING carrier to SERVER: {REQUEST_MESSAGE.COMMAND[:2].hex()}")
        conn[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[:2])
        await conn[device.DEV_PORT][1][1].drain()
        # print(f"SENDING REQ DATA to SERVER: {REQUEST_MESSAGE.COMMAND[1:].hex()}")
        conn[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[1:])
        await conn[device.DEV_PORT][1][1].drain()
        bytesToRead: bytes = await conn[device.DEV_PORT][1][0].read(1)
        # print(f"CLIENT READING LENGTH: {bytesToRead}")
        data = bytearray(await conn[device.DEV_PORT][1][0].readexactly(
                int.from_bytes(
                        bytesToRead,
                        byteorder='little',
                        signed=False
                        )
                )
                         )
        
        RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
        
        if data[2] == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
            device.ext_srv_notification = RETURN_MESSAGE
        else:
            raise TypeError
    
    except TypeError as type_error:
        connected_devices[device.DEV_PORT].pop()
        device.dev_srv_connected = False
        raise TypeError(print(f"[DEV_CONNECT_SRV]-[MSG]: WRONG REPLY... SOMETHING IS WRONG")) from type_error
    except ConnectionError as e:
        conn.clear()
        device.dev_srv_connected = False
        print(f"CAN'T ESTABLISH CONNECTION TO SERVER...{e.args}")
        raise ConnectionError(e.args)
    else:
        connected_devices[device.DEV_PORT] = conn[device.DEV_PORT]
        connected_devices[device.DEV_PORT][0].ext_srv_notification = RETURN_MESSAGE
        device.dev_srv_connected = True
        print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION ESTABLISHED...")
        print(f"[{connected_devices[device.DEV_PORT][0].DEV_NAME}:"
              f"{connected_devices[device.DEV_PORT][0].DEV_PORT.hex()}]-[{RETURN_MESSAGE.m_cmd_code_str}]: ["
              f"{RETURN_MESSAGE.m_event_str!s}]")
        return True


async def DEV_DISCONNECT(connected_devices: {
        bytes: [Device, [StreamReader, StreamWriter]]
        },
                         device: Device,
                         host: str = '127.0.0.1',
                         port: int = 8888) -> bool:
    DISCONNECT_MSG: EXT_SRV_DISCONNECTED_SND = EXT_SRV_DISCONNECTED_SND(port=device.DEV_PORT)
    
    connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND[0])
    connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND)
    await connected_devices[device.DEV_PORT][1][1].drain()
    await connected_devices[device.DEV_PORT][1][1].close()
    connected_devices.pop(device.DEV_PORT)
    return True


async def CMD_SND(connected_devices: {
        bytes: [Device, [StreamReader, StreamWriter]]
        },
        message: DOWNSTREAM_MESSAGE) -> bool:
    
    sndCMD = message
    while not await connected_devices[sndCMD.port][0].wait_ext_server_connected():
        print('', end="WAITING FOR SERVER CONNECTION...")
    else:
        print(f"SENDING COMMAND TO SERVER: {sndCMD.COMMAND.hex()}")
        print(connected_devices[sndCMD.port][1][1].get_extra_info('peername'))
        connected_devices[sndCMD.port][1][1].write(sndCMD.COMMAND[1])
        connected_devices[sndCMD.port][1][1].write(sndCMD.COMMAND)
        await connected_devices[sndCMD.port][1][1].drain()
    return True


async def DEV_LISTEN_SRV(connected_devices: {
        bytes: [Device, [StreamReader, StreamWriter]]
        },
                         device: ADevice,
                         host: str = '127.0.0.1',
                         port: int = 8888) -> bool:
    con_attempts = max_attempts = 10
    data: bytearray
    
    # main loop:
    while con_attempts > 0:
        if device.DEV_PORT not in connected_devices.keys():
            con_attempts -= 1
            print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: ATTEMPTING TO REGISTER WITH SERVER...")
            try:
                future_connection = asyncio.ensure_future(DEV_CONNECT_SRV(connected_devices=connected_devices,
                                                                          device=device))
                await asyncio.wait_for(future_connection, timeout=5.0)
            
            except (TimeoutError, ConnectionError) as e:
                if isinstance(e, TimeoutError):
                    print(f"CONNECTION TIMED OUT: {e.args}...")
                    print(f"[CONNECT_LISTEN_SRV]-[MSG]: TIMEOUT ERROR DURING CONNECTION ATTEMPT... RETRYING "
                          f"{con_attempts}/{max_attempts}...")
                if isinstance(e, ConnectionError):
                    print(f"CONNECTION: {e.args}...")
                    print(f"[CONNECT_LISTEN_SRV]-[MSG]: CONNECTION ERROR DURING CONNECTION ATTEMPT... RETRYING "
                          f"{con_attempts}/{max_attempts}...")
                if con_attempts == 0:
                    raise
                continue
            
            else:
                print(f"[CONNECT_LISTEN_SRV]-[MSG]: DEVICE SUCCESSFULLY CONNECTED...")
                continue
        else:
            try:
                con_attempts = max_attempts - 1
                print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
                future_listening_srv = asyncio.ensure_future(await connected_devices[device.DEV_PORT][1][0].read(1))
                await asyncio.wait_for(future_listening_srv, timeout=5.0)
                
                bytesToRead: bytes = future_listening_srv.result()
                print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: READING "
                      f"{int.from_bytes(bytesToRead, byteorder='little', signed=False)} BYTES")
                data = await connected_devices[device.DEV_PORT][1][0].readexactly(n=int.from_bytes(
                        bytesToRead,
                        byteorder='little',
                        signed=False)
                        )
                RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
                if RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_PORT_VALUE:
                    device.port_value = RETURN_MESSAGE
                elif RETURN_MESSAGE.m_type == MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK:
                    device.cmd_status.m_type = RETURN_MESSAGE
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
                else:
                    raise TypeError
            
            except TimeoutError as e:
                print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: TIMEOUT... again...")
                if con_attempts == 0:
                    raise TimeoutError(print, e.args)
                continue
            except (KeyError, KeyboardInterrupt) as e:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            except (ConnectionError, ConnectionResetError, ConnectionRefusedError) as e:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                if con_attempts == 0:
                    raise
                else:
                    print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {con_attempts}/{max_attempts}...")
                    continue
            except Exception as e:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT] = {b'', (None, (None, None))}
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from e
            else:
                print(f"[{device.DEV_NAME.decode()!s}:{device.DEV_PORT.hex()!s}]-"
                      f"[{RETURN_MESSAGE.m_cmd_feedback_str!s}]: "
                      f"RECEIVED [DATA] = [{RETURN_MESSAGE.COMMAND!s}]")
                continue
    return False


if __name__ == '__main__':
    connected_devices: {
            bytes: [Device, [StreamReader, StreamWriter]]
            } = {}
    cmd_sequence = CMD_Sequence()
    # Creating client object
    HUB = Hub(name="THE LEGO HUB 2.0")
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67)
    STR = SingleMotor(name="STR", port=b'\x02')
    FWD_RWD = SynchronizedMotor(name="FWD_RWD", motor_a=FWD, motor_b=RWD)
    
    loop = asyncio.get_event_loop()
    try:
        CONNECTION_SEQ = {
                'HUB_CON': DEV_LISTEN_SRV(connected_devices=connected_devices, device=HUB),
                'FWD_CON': DEV_LISTEN_SRV(connected_devices=connected_devices, device=FWD),
                'RWD_CON': DEV_LISTEN_SRV(connected_devices=connected_devices, device=RWD),
                'STR_CON': DEV_LISTEN_SRV(connected_devices=connected_devices, device=STR),
                }
        cmd_sequence.
        loop.run_until_complete(asyncio.wait_for(HUB_CON, timeout=None))
        loop.run_until_complete(asyncio.wait_for(FWD_CON, timeout=None))
        loop.run_until_complete(asyncio.wait_for(RWD_CON, timeout=None))
        loop.run_until_complete(asyncio.wait_for(STR_CON, timeout=None))
        
        loop.run_forever()
    except (ConnectionError, TypeError, RuntimeError, Exception) as e:
        print(f'[CMD_CLIENT]-[MSG]: SERVER DOWN OR CONNECTION REFUSED... COMMENCE SHUTDOWN...')
        loop.stop()
    finally:
        loop.close()
        print(f'[CMD_CLIENT]-[MSG]: SHUTDOWN COMPLETED...')
