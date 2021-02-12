import asyncio
from asyncio.streams import StreamReader, StreamWriter

from LegoBTLE.Device.messaging import Message
connectionListWriter = {}
connectionListReader = {}


async def handle_echo(reader: StreamReader, writer: StreamWriter):
    
    data = await reader.readuntil(b' ')
    message = Message(data[0:(len(data)-1)])
    addr = writer.get_extra_info('peername')
    if message.port not in connectionListWriter.keys():
        connectionListWriter[message.port] = writer
        connectionListReader[message.port] = reader
    print(f"Received {message.payload!r} from {addr!r}")
    
    print(f"ECHO Send: {message.payload!r} to {addr}")
    connectionListWriter.get(message.port).write(data)
    await writer.drain()
    await asyncio.sleep(.8)
    init_msg = bytearray(b'\x0f\x00\x04' + message.port + b'\x01\x2f\x00\x00\x10\x00\x00\x00\x10\x00\x00')
    init_msg.extend(b' ')
    connectionListWriter.get(Message(init_msg).port).write(init_msg)
    await connectionListWriter.get(Message(init_msg).port).drain()
    print(f"sent init: {init_msg} to {addr}")
    # writer.close()


async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
