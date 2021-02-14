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
from asyncio.streams import StreamReader, StreamWriter

from LegoBTLE.Device.messaging import Message

connectedWriter = {}
connectedReader = {}


async def handle_echo(reader: StreamReader, writer: StreamWriter):
    while True:
        try:
            print(await reader.readuntil(b' '))
            writer.write(b'\x07\x00\x00' + b'\x02' + b'\x00\x01' + b' ')
        except ConnectionResetError:
            print(f'CLIENT DISCONNECTED...')
            break
    # message = Message(await reader.readuntil(b' '))
    # addr = writer.get_extra_info('peername')
    # if message.port not in connectedWriter.keys():
    #     connectedWriter[message.port] = writer
    #     connectedReader[message.port] = reader
    # else:
    #     print(f'Client {connectedReader[message.port]} already connected...')
    #
    # print(f"Received {message.payload!r} from {addr!r}")
    #
    # ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x01' + b' '))
    # print(f"Sending ACK: {ret_msg.payload!r} to {connectedWriter.get(ret_msg.port).get_extra_info('peername')}")
    # connectedWriter.get(message.port).write(ret_msg.payload)
    # await asyncio.sleep(.8)
    # await connectedWriter.get(ret_msg.port).drain()
    # print(f"sent init: {ret_msg} to {addr}")
    #
    # while True:
    #     await reader.readuntil(b' ')
    

async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'[{addr[0]}:{addr[1]}]-[MSG]: SERVER RUNNING...')
    
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    loop.run_forever()
