import asyncio
from random import randint, random, uniform


async def handle_echo(reader, writer):
    data = await reader.readuntil(b' ')
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message!r} from {addr!r}")
    data = data + randint(1, 8).to_bytes(1, 'little') + b' '
    print(f"Send: {data!r}")
    writer.write(data)
    await writer.drain()
    data = b'EXTRADATA' + randint(1, 8).to_bytes(1, 'little') + b' '
    print(f"Send: {data!r} TO {addr!r}")
    writer.write(data)
    await writer.drain()
    await asyncio.sleep(3)
    for i in range(1, 30):
        data = b'EXTRADATALATE:' + i.to_bytes(length=1, byteorder='little') + randint(1, 8).to_bytes(1, 'little') + b' '
        print(f"Send: {data!r} TO {addr!r}")
        await asyncio.sleep(uniform(.1, .9))
        writer.write(data)
        await writer.drain()
    

async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)
    
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':

    asyncio.run(main())