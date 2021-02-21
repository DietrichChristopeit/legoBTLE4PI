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


async def connectDevice(name: str = 'DEVICE', host: str = '0.0.0.0', port: int = -1, motorport: bytes = b'\xff') -> (
        StreamReader,
        StreamWriter):
    reader, writer = await asyncio.open_connection(host, port)
    reg_msg: bytearray = bytearray(b'\x07\x00\x00' + motorport + b'\x00\x00' + b' ')
    writer.write(reg_msg)
    return_msg = Message(await reader.readuntil(b' '))
    if (return_msg.m_type == b'SERVER_ACTION') and (return_msg.return_code == b'ACK'):
        print(f'[{name}]-[RCV]: [{return_msg.m_type}]-[{return_msg.cmd}] = '
              f'[{return_msg.return_code.decode("utf-8")}]...')
        connected.set()
    return reader, writer


async def REC_MSG(reader: StreamReader):
    if await event_wait(connected, 2):
        while not await event_wait(terminate, .1):
            data = await reader.readuntil(b' ')
            await asyncio.sleep(uniform(.1, .5))
            # await asyncio.wait_for(data, timeout=-1)
            print(f'Received: {data!r}')


async def main():
    global SERVER_IP
    global SERVER_PORT
    
    coro = asyncio.create_task(connectDevice(name='FRONTWHEELDRIVE', host=SERVER_IP, port=SERVER_PORT,
                                             motorport=b'\x00'),
                               name='FRONTWHEELDRIVE')
    coro1 = asyncio.create_task(connectDevice(name='REARWHEELDRIVE', host=SERVER_IP, port=SERVER_PORT,
                                              motorport=b'\x01'),
                                name='REARWHEELDRIVE')
    futs = await asyncio.wait((coro, coro1))
    print(futs)
    
    #while not await event_wait(terminate, .1):
    #    rec = asyncio.create_task(RCV_MSG(None))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # asyncio.run(main())
    asyncio.run_coroutine_threadsafe(main(), loop)
    loop.run_forever()
