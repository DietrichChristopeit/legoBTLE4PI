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

from tabulate import tabulate

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


async def DEV_CONNECT_SRV(connected_devices: {}, device: Device, host: str = '127.0.0.1', port: int = 8888) -> bool:
    try:
        device.ext_srv_notification = None
        connected_devices.clear()
            x = {device.DEV_PORT: (device, await asyncio.open_connection(host=host, port=port))}
        REQUEST_MESSAGE = CMD_EXT_SRV_CONNECT_REQ(port=device.DEV_PORT)
        # print(f"SENDING REQ to SERVER: {REQUEST_MESSAGE.COMMAND.hex()}")
        # print(f"SENDING carrier to SERVER: {REQUEST_MESSAGE.COMMAND[:2].hex()}")
        connected_devices[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[:2])
        await connected_devices[device.DEV_PORT][1][1].drain()
        # print(f"SENDING REQ DATA to SERVER: {REQUEST_MESSAGE.COMMAND[1:].hex()}")
        connected_devices[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[1:])
        await connected_devices[device.DEV_PORT][1][1].drain()
        bytesToRead: bytes = await connected_devices[device.DEV_PORT][1][0].read(1)
        # print(f"CLIENT READING LENGTH: {bytesToRead}")
        data = await connected_devices[device.DEV_PORT][1][0].readexactly(
                int.from_bytes(
                        bytesToRead,
                        byteorder='little',
                        signed=False
                        )
                )
        
        RETURN_MESSAGE = UpStreamMessageBuilder(data).build()
        
        if data[2] == int(MESSAGE_TYPE.UPS_DNS_HUB_ACTION.hex(), 16):
            device.hub_action_notification = RETURN_MESSAGE
        
        elif data[2] == int(MESSAGE_TYPE.UPS_HUB_ATTACHED_IO.hex(), 16):
            device.hub_attached_io_notification = RETURN_MESSAGE
        
        elif data[2] == int(MESSAGE_TYPE.UPS_HUB_GENERIC_ERROR.hex(), 16):
            device.generic_error_notification = RETURN_MESSAGE
        
        elif data[2] == int(MESSAGE_TYPE.UPS_PORT_CMD_FEEDBACK.hex(), 16):
            device.cmd_feedback_notification = RETURN_MESSAGE
        elif data[2] == int(MESSAGE_TYPE.UPS_PORT_VALUE.hex(), 16):
            device.port_value = RETURN_MESSAGE
        
        elif data[2] == int(MESSAGE_TYPE.UPS_PORT_NOTIFICATION.hex(), 16):
            device.port_notification = RETURN_MESSAGE
        
        elif data[2] == int(MESSAGE_TYPE.UPS_DNS_EXT_SERVER_CMD.hex(), 16):
            device.ext_srv_notification = RETURN_MESSAGE
        else:
            raise TypeError
    
    except TypeError as type_error:
        connected_devices[device.DEV_PORT].pop()
        device.dev_srv_connected = False
        raise TypeError(print(f"[DEV_CONNECT_SRV]-[MSG]: WRONG REPLY... SOMETHING IS WRONG")) from type_error
    except ConnectionError:
        connected_devices[device.DEV_PORT].pop()
        device.dev_srv_connected = False
        print(f"CAN'T ESTABLISH CONNECTION TO SERVER...")
        return False
    else:
        connected_devices[device.DEV_PORT][0].ext_srv_notification = RETURN_MESSAGE
        device.dev_srv_connected = True
        print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION ESTABLISHED...")
        print(f"[{connected_devices[device.DEV_PORT][0].DEV_NAME}:"
              f"{connected_devices[device.DEV_PORT][0].DEV_PORT.hex()}]-[{RETURN_MESSAGE.m_cmd_code_str}]: ["
              f"{RETURN_MESSAGE.m_event_str!s}]")
        return True


async def DEV_DISCONNECT(connected_devices: {}, device: Device, host: str = '127.0.0.1', port: int = 8888) -> bool:
    DISCONNECT_MSG: EXT_SRV_DISCONNECTED_SND = EXT_SRV_DISCONNECTED_SND(port=device.DEV_PORT)
    
    connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND[0])
    connected_devices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND)
    await connected_devices[device.DEV_PORT][1][1].drain()
    await connected_devices[device.DEV_PORT][1][1].close()
    connected_devices.pop(device.DEV_PORT)
    return True


async def CMD_SND(connected_devices: {}, MESSAGE: DOWNSTREAM_MESSAGE) -> bool:
    sndCMD = MESSAGE
    while not await connected_devices[sndCMD.port][0].wait_ext_server_connected():
        print('', end="WAITING FOR SERVER CONNECTION...")
    else:
        print(f"SENDING COMMAND TO SERVER: {sndCMD.COMMAND.hex()}")
        print(connected_devices[sndCMD.port][1][1].get_extra_info('peername'))
        connected_devices[sndCMD.port][1][1].write(sndCMD.COMMAND[1])
        connected_devices[sndCMD.port][1][1].write(sndCMD.COMMAND)
        await connected_devices[sndCMD.port][1][1].drain()
    return True


async def DEV_LISTEN_SRV(connected_devices: {}, device: ADevice, host: str = '127.0.0.1', port: int = 8888):
    con_attempts: int = 10
    read_attempts = 10
    data: bytearray
    
    # main loop:
    while con_attempts > 0:
        if device.DEV_PORT not in connected_devices.keys():
            con_attempts -= 1
            print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: ATTEMPTING TO REGISTER WITH SERVER...")
            try:
                fut = asyncio.ensure_future(DEV_CONNECT_SRV(connected_devices=connected_devices, device=device))
                await asyncio.wait_for(fut, timeout=5.0)
            except asyncio.TimeoutError:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT].pop()
                print(f"[CONNECT_LISTEN_SRV]-[MSG]: TIMEOUT OCCURRED DURING CONNECTION ATTEMPT... RETRYING 10 TIMES...")
                continue
        else:
            try:
                print(f"[{device.DEV_NAME}:{device.DEV_PORT.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
                fut = asyncio.ensure_future(await connected_devices[device.DEV_PORT][1][0].read(1))
                await asyncio.wait_for(fut, timeout=5.0)
                print("TIMEOUT")
                bytesToRead: bytes = fut.result()
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
            except Exception as general_exception:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT].pop()
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from general_exception
            except KeyError as key_error:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT].pop()
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from key_error
            except KeyboardInterrupt as keyboard_interrupt:
                device.dev_srv_connected = False
                connected_devices[device.DEV_PORT].pop()
                raise Exception(print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: UNEXPECTED "
                                      f"ERROR... GIVING UP...")) from keyboard_interrupt
            except ConnectionResetError:
                read_attempts -= 1
                if read_attempts > 0:
                    print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {10 - read_attempts}/10 TIMES...")
        
                    continue
            except ConnectionRefusedError:
                read_attempts -= 1
                if read_attempts > 0:
                    print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {10 - read_attempts}/10 TIMES...")
        
                    continue
            except ConnectionError as wait_msg_exception:
                read_attempts -= 1
                if read_attempts > 0:
                    print(f"[{device.DEV_NAME!s}:{device.DEV_PORT.hex()!s}]-[MSG]: CONNECTION "
                          f"ERROR... RETRYING {10 - read_attempts}/10 TIMES...")
                    
                    continue
                raise ConnectionError(print(f"[CONNECT_LISTEN_SRV]-[MSG]:"
                                            f"maximum number of connection attempts reached... giving up...")) \
                    from wait_msg_exception
            else:
                print(f"[{device.DEV_NAME.decode()!s}:{device.DEV_PORT.hex()!s}]-"
                      f"[{RETURN_MESSAGE.m_cmd_feedback_str!s}]: "
                      f"RECEIVED [DATA] = [{RETURN_MESSAGE.COMMAND!s}]")
                continue
    
    device.dev_srv_connected = False
    connected_devices[device.DEV_PORT].pop()
    print(f"[CONNECT_LISTEN_SRV]-[MSG]: maximum number of connection attempts reached... giving up...")
    return


if __name__ == '__main__':
    conneccted_devices: {} = {}
    
    
    async def INIT_AND_LISTEN() -> list:
        return [
                await asyncio.create_task(DEV_LISTEN_SRV(connected_devices=conneccted_devices, device=HUB)),
                # await asyncio.create_task(DEV_CONNECT_SRV(RWD)),
                # await asyncio.create_task(DEV_CONNECT(FWD)),
                # await asyncio.create_task(DEV_CONNECT(STR)),
                ]
    
    
    # async def LISTEN_DEV() -> list:
    #     return [
    #             asyncio.create_task(MSG_RCV(HUB)),
    #             # asyncio.create_task(MSG_RCV(FWD)),
    #             # asyncio.create_task(MSG_RCV(RWD)),
    #             # asyncio.create_task(MSG_RCV(STR)),
    #             ]
    
    # Creating client object
    HUB = Hub(name="THE LEGO HUB 2.0")
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67)
    STR = SingleMotor(name="STR", port=b'\x02')
    FWD_RWD = SynchronizedMotor(name="FWD_RWD", motor_a=FWD, motor_b=RWD)
    
    loop = asyncio.get_event_loop()
    try:
        
        loop.run_until_complete(asyncio.wait((INIT_AND_LISTEN(),), return_when='ALL_COMPLETED'))
        
        # loop.run_until_complete(asyncio.wait((LISTEN_DEV(),), timeout=.9))
        
        # CMDs come here
        
        # loop.run_until_complete(asyncio.sleep(5.0))
        # loop.run_until_complete(CMD_SND(HUB.EXT_SRV_CONNECT_REQ()))
        # loop.run_until_complete(CMD_SND(STR.REQ_PORT_NOTIFICATION()))
        # loop.run_until_complete(CMD_SND(FWD.REQ_PORT_NOTIFICATION()))
        # loop.run_until_complete(asyncio.wait((FWD_RWD.GOTO_ABS_POS(abs_pos_a=50,
        #                                                                 abs_pos_b=60,
        #                                                                 abs_max_power=90,
        #                                                                 on_completion=MOVEMENT.COAST), )))
        # loop.run_until_complete(CMD_SND(RWD.REQ_PORT_NOTIFICATION()))
        # loop.run_until_complete(CMD_SND(FWD_RWD.VIRTUAL_PORT_SETUP(connect=True)))
        # loop.run_until_complete(CMD_SND(FWD_RWD.GOTO_ABS_POS(abs_pos_a=50,
        #                                                            abs_pos_b=60,
        #                                                            abs_max_power=90,
        #                                                            on_completion=MOVEMENT.COAST)))
        
        # loop.run_until_complete(CMD_SND(STR, STR.turnForT, 5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK))
        # loop.run_until_complete(CMD_SND(FWD, FWD.turnForT, 5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK))
        
        # sync def PARALLEL() -> list:
        #    return [
        #        await asyncio.create_task(
        #            CMD_SND(RWD.CMD_START_SPEED_TIME(
        #                power=70,
        #                time=10000,
        #                direction=MOVEMENT.FORWARD,
        #                on_completion=MOVEMENT.HOLD))),
        #        await asyncio.create_task(
        #            CMD_SND(FWD.CMD_START_SPEED_TIME(
        #                power=70,
        #                time=10000,
        #                direction=MOVEMENT.REVERSE,
        #                on_completion=MOVEMENT.COAST))),
        #        ]
        
        # loop.run_until_complete(asyncio.wait_for((asyncio.ensure_future(PARALLEL())), timeout=None))
        # loop.run_until_complete(CMD_SND(FWD.GOTO_ABS_POS(abs_pos=90, speed=100)))
        
        loop.run_forever()
    except ConnectionRefusedError:
        print(f'[CMD_CLIENT]-[MSG]: SERVER DOWN OR CONNECTION REFUSED... COMMENCE SHUTDOWN...')
        loop.stop()
    finally:
        loop.close()
        print(f'[CMD_CLIENT]-[MSG]: SHUTDOWN COMPLETED...')
