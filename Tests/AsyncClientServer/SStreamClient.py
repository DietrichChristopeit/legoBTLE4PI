import asyncio
import concurrent.futures
from asyncio import StreamReader, StreamWriter
from random import uniform


async def get_new_conn() -> (StreamReader, StreamWriter):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)
    return reader, writer


async def tcp_echo_client(message, reader: StreamReader, writer: StreamWriter):
    print(f'Send: {message!r}')
    writer.write(message.encode())
    
    while True:
        data = await reader.readuntil(b' ')
        await asyncio.sleep(uniform(.1, .5))
        # await asyncio.wait_for(data, timeout=-1)
        print(f'Received: {data!r}')


async def main():
    loop = asyncio.get_running_loop()
    (r1, w1) = await get_new_conn()
    (r2, w2) = await get_new_conn()
    t = asyncio.create_task(tcp_echo_client('11111HelloWorld! ', r1, w1))
    t1 = asyncio.create_task(tcp_echo_client('22222HelloWorld! ', r2, w2))
    # t2 = asyncio.create_task(tcp_echo_client('afds World!', r2, w2))
    await t
    await t1
    # await  t2
    
    while True:
        pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(main(), loop)
    loop.run_forever()
