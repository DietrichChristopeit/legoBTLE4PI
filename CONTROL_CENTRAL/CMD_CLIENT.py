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

import asyncio
import contextlib

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AMotor import SingleMotor
from LegoBTLE.LegoWP.commands.downstream import (CMD_START_SPEED_TIME, DownStreamMessage, EXT_SRV_CONNECT_REQ,
                                                 EXT_SRV_DISCONNECTED_SND,
                                                 PORT_NOTIFICATION_REQ)
from LegoBTLE.LegoWP.commands.upstream import (EXT_SERVER_MESSAGE_RCV, UpStreamMessage)
from LegoBTLE.LegoWP.types import MOVEMENT

connectedDevices = {}


async def event_wait(evt, timeout):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def DEV_CONNECT(device: Device, host: str = '127.0.0.1', port: int = 8888):
    try:
        connectedDevices[device.DEV_PORT] = (device, (await asyncio.open_connection(host=host, port=port)))
    except ConnectionRefusedError:
        raise ConnectionRefusedError
    
    REQUEST_MESSAGE = EXT_SRV_CONNECT_REQ(port=device.DEV_PORT)
    connectedDevices[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND[0])
    connectedDevices[device.DEV_PORT][1][1].write(REQUEST_MESSAGE.COMMAND)
    
    await connectedDevices[device.DEV_PORT][1][1].drain()
    
    bytesToRead: int = await connectedDevices[device.DEV_PORT][1][0].read(1)
    RETURN_MESSAGE = UpStreamMessage(await connectedDevices[device.DEV_PORT][1][0].read(bytesToRead)).get_Message()
    
    assert isinstance(RETURN_MESSAGE, EXT_SERVER_MESSAGE_RCV)
    try:
        print(f'[{connectedDevices[device.DEV_PORT][0].name}:'
              f'{connectedDevices[device.DEV_PORT][0].DEV_PORT.hex()}]-[{RETURN_MESSAGE.m_cmd_code_str}]: ['
              f'{RETURN_MESSAGE.m_event_str}]')
    except AssertionError:
        print(f"RETURN MESSAGE IS NOT A EXT_SERVER_MESSAGE_RCV")
        raise TypeError
    return


async def DEV_DISCONNECT(device: Device, host: str = '127.0.0.1', port: int = 8888) -> bool:
    DISCONNECT_MSG: EXT_SRV_DISCONNECTED_SND = EXT_SRV_DISCONNECTED_SND(port=device.DEV_PORT).COMMAND
    
    connectedDevices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND[0])
    connectedDevices[device.DEV_PORT][1][1].write(DISCONNECT_MSG.COMMAND)
    await connectedDevices[device.DEV_PORT][1][1].drain()
    await connectedDevices[device.DEV_PORT][1][1].close()
    connectedDevices.pop(device.DEV_PORT)
    return True


async def CMD_SND(COMMAND: DownStreamMessage) -> bool:
    sndCMD = COMMAND.get_Message()
    print(sndCMD.COMMAND)
    print(connectedDevices[sndCMD.port][1][1].get_extra_info('peername'))
    connectedDevices[sndCMD.port][1][1].write(sndCMD.COMMAND[0])
    connectedDevices[sndCMD.port][1][1].write(sndCMD.COMMAND)
    await connectedDevices[sndCMD.port][1][1].drain()
    
    return True


async def MSG_RCV(device):
    while True:
        try:
            print(f"[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[MSG]: LISTENING FOR SERVER MESSAGES...")
            
            bytesToRead = await connectedDevices[device.DEV_PORT][1][0].read(1)
            RETURN_MESSAGE = UpStreamMessage(await connectedDevices[device.DEV_PORT][1][0].
                                             read(bytesToRead)).get_Message()
            
            # if self._data[2] == M_TYPE.UPS_DNS_HUB_ACTION:
            #    return HUB_ACTION_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_HUB_ATTACHED_IO:
            #    return HUB_ATTACHED_IO_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_HUB_GENERIC_ERROR:
            #    return HUB_GENERIC_ERROR_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_COMMAND_STATUS:
            #    return HUB_CMD_STATUS_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_PORT_VALUE:
            #    return HUB_PORT_VALUE_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_PORT_NOTIFICATION:
            #    return HUB_PORT_NOTIFICATION_RCV(self._data)
            #
            # elif self._data[2] == M_TYPE.UPS_DNS_EXT_SERVER_CMD:
            #    return EXT_SERVER_CONNECT_RCV(self._data)
            # else:
            #    raise TypeError
            
            print(
                f"[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[{RETURN_MESSAGE.m_cmd_status_str}]: RECEIVED ["
                f"DATA] = [{RETURN_MESSAGE.COMMAND}]")
        except ConnectionResetError:
            print(f'[{device.DEV_NAME.decode()}:{device.DEV_PORT.hex()}]-[MSG]: DEVICE DISCONNECTED...')
            connectedDevices.pop(device.DEV_PORT)
            break
    return


if __name__ == '__main__':
    
    async def INIT() -> list:
        return [
            await asyncio.create_task(DEV_CONNECT(RWD)),
            await asyncio.create_task(DEV_CONNECT(FWD)),
            await asyncio.create_task(DEV_CONNECT(STR)),
            ]
    
    
    async def LISTEN_DEV() -> list:
        return [
            asyncio.create_task(MSG_RCV(FWD)),
            asyncio.create_task(MSG_RCV(RWD)),
            asyncio.create_task(MSG_RCV(STR)),
            ]
    
    
    # Creating client object
    terminate: asyncio.Event = asyncio.Event()
    FWD = SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67, terminate=terminate)
    RWD = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67, terminate=terminate)
    STR = SingleMotor(name="STR", port=b'\x02', gearRatio=2.67, terminate=terminate)
    
    loop = asyncio.get_event_loop()
    try:
        
        loop.run_until_complete(
            asyncio.wait((asyncio.ensure_future(INIT()),), return_when='ALL_COMPLETED', timeout=300))
        
        loop.run_until_complete(asyncio.wait((asyncio.ensure_future(LISTEN_DEV()),), timeout=.9))
        
        # CMDs come here
        
        # loop.run_until_complete(asyncio.sleep(5.0))
        loop.run_until_complete(CMD_SND(STR.PORT_NOTIFICATION_REQ()))
        loop.run_until_complete(CMD_SND(FWD.PORT_NOTIFICATION_REQ()))
        loop.run_until_complete(CMD_SND(RWD.PORT_NOTIFICATION_REQ()))
        
        
        # loop.run_until_complete(CMD_SND(STR, STR.turnForT, 5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK))
        # loop.run_until_complete(CMD_SND(FWD, FWD.turnForT, 5000, MotorConstant.FORWARD, 50, MotorConstant.BREAK))
        
        async def PARALLEL() -> list:
            return [
                await asyncio.create_task(
                    CMD_SND(RWD, CMD_START_SPEED_TIME(port=RWD.DEV_PORT,
                                                      power=70,
                                                      time=10000,
                                                      direction=MOVEMENT.FORWARD,
                                                      on_completion=MOVEMENT.HOLD))),
                await asyncio.create_task(
                    CMD_SND(FWD, CMD_START_SPEED_TIME(port=FWD.DEV_PORT,
                                                      power=70,
                                                      time=10000,
                                                      direction=MOVEMENT.REVERSE,
                                                      on_completion=MOVEMENT.COAST))),
                ]
        
        
        # make it simpler
        loop.run_until_complete(asyncio.wait_for((asyncio.ensure_future(PARALLEL())), timeout=None))
        loop.run_until_complete(CMD_SND(FWD, FWD.GOTO_ABS_POS(abs_pos=90, speed=100)))
        
        loop.run_forever()
    except ConnectionRefusedError:
        print(f'[CMD_CLIENT]-[MSG]: SERVER DOWN OR CONNECTION REFUSED... COMMENCE SHUTDOWN...')
        loop.stop()
    finally:
        loop.close()
        print(f'[CMD_CLIENT]-[MSG]: SHUTDOWN COMPLETED...')
