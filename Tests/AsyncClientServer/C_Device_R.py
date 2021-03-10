import asyncio
import contextlib
from asyncio import StreamReader, StreamWriter
from random import uniform

# only for covenience

from LegoBTLE.Device.old.messaging import Message

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888
connected: asyncio.Event = asyncio.Event()
terminate: asyncio.Event = asyncio.Event()


async def event_wait(evt, timeout):
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


class DeviceClient:
    
    def __init__(self,
                 name: str = 'HUB_DEVICE',
                 host: str = '127.0.0.1',
                 serverport: int = 8888,
                 hubdeviceport: bytes = b'\xff'):
        
        self._name = name
        self._host = host
        self._serverport = serverport
        self._hubdeviceport = hubdeviceport
        self._reader: StreamReader = None
        self._writer: StreamWriter = None
    
    async def connectDevice(self) -> bool:
        
        self._reader, self._writer = await asyncio.open_connection(self._host, self._serverport)
        reg_msg: bytearray = bytearray(b'\x07\x00\x00' + self._hubdeviceport + b'\x00\x00' + b' ')
        self._writer.write(reg_msg)
        await self._writer.drain()
        
        return_msg = Message(await self._reader.readuntil(b' '))
        if (return_msg.m_type == b'SND_SERVER_ACTION') and (return_msg.return_code == b'ACK'):
            print(f'[{self._name}]-[RCV]: [{return_msg.m_type.decode()}]-[{return_msg.cmd.decode()}] = '
                  f'[{return_msg.return_code.decode()}]...')
            connected.set()
        return True
    
    async def RCV_MSG(self):
        #if await event_wait(connected, 2):
        #while True:
        r = await self._reader.read(100)
        return_msg = Message(r)
        await asyncio.sleep(uniform(.1, .5))
        # await asyncio.wait_for(data, timeout=-1)
        print(f'[{self._name}]-[RCV]: [{return_msg.m_type.decode()}]-[{return_msg.cmd.decode()}] = '
              f'[{return_msg.return_code.decode()}]...')

    async def SND_MSG(self) -> bool:
        #if await event_wait(connected, 2):
        #while not await event_wait(terminate, .1):
        self._writer.write(bytearray(b'\x07\x00\x00' + self._hubdeviceport + b'\x01\x00' + b' '))
        await self._writer.drain()
        return True


async def main(looper):
    C_FWD = DeviceClient(name='FRONTWHEELDRIVE', hubdeviceport=b'\x00')
    T_FWD = await asyncio.create_task(C_FWD.connectDevice(), name='FRONTWHEELDRIVE')
    #T_READ_FWD = asyncio.run_coroutine_threadsafe(await C_FWD.RCV_MSG(), asyncio.get_running_loop())
    
    C_RWD = DeviceClient(name='REARWHEELDRIVE', hubdeviceport=b'\x01')
    T_RWD = await asyncio.create_task(C_RWD.connectDevice(), name='REARWHEELDRIVE')
    #T_READ_RWD = asyncio.run_coroutine_threadsafe(await C_RWD.RCV_MSG(), asyncio.get_running_loop())
    
    C_STR = DeviceClient(name='STEERING', hubdeviceport=b'\x02')
    T_STR = await asyncio.create_task(C_STR.connectDevice(), name='STEERING')
    #T_READ_STR = asyncio.run_coroutine_threadsafe(await C_STR.RCV_MSG(), asyncio.get_running_loop())
    await asyncio.create_task(C_STR.SND_MSG(), name='Lalles')
    asyncio.run_coroutine_threadsafe(C_STR.RCV_MSG(), looper)
    
    # while not await event_wait(terminate, .1):
     #   rec = await C_STR.RCV_MSG()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # asyncio.run(main())
    C_FWD = DeviceClient(name='FRONTWHEELDRIVE', hubdeviceport=b'\x00')
    T_FWD = asyncio.run(C_FWD.connectDevice())
    # T_READ_FWD = asyncio.run_coroutine_threadsafe(await C_FWD.RCV_MSG(), asyncio.get_running_loop())

    C_RWD = DeviceClient(name='REARWHEELDRIVE', hubdeviceport=b'\x01')
    T_RWD = asyncio.run(C_RWD.connectDevice())
    # T_READ_RWD = asyncio.run_coroutine_threadsafe(await C_RWD.RCV_MSG(), asyncio.get_running_loop())

    C_STR = DeviceClient(name='STEERING', hubdeviceport=b'\x02')
    T_STR = asyncio.run(C_STR.connectDevice())
    # T_READ_STR = asyncio.run_coroutine_threadsafe(await C_STR.RCV_MSG(), asyncio.get_running_loop())
    asyncio.run(C_STR.SND_MSG())
    asyncio.run_coroutine_threadsafe(C_STR.RCV_MSG(), loop)
    # asyncio.run_coroutine_threadsafe(main(event_loop), event_loop)
    loop.run_forever()
