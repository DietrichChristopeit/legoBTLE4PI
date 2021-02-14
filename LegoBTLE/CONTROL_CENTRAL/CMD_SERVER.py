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

connectedDevices = {}


async def listen_clients(reader: StreamReader, writer: StreamWriter):
    while True:
        try:
            message = Message(await reader.readuntil(b' '))
            addr = writer.get_extra_info('peername')
            if message.port not in connectedDevices.keys():
                connectedDevices[message.port] = (reader, writer)
            else:
                print(f'[{addr[0]}:{addr[1]}]: already connected...')
            
            print(f"Received {message.payload!r} from {addr!r}")
            ret_msg: Message = Message()
            
            if message.m_type == b'SND_SERVER_ACTION':
                if message.return_code == b'DCD':
                    print(f"DISCONNECTING DEVICE...")
                    await connectedDevices[message.port][0].close()
                    await connectedDevices[message.port][1].close()
                    connectedDevices.pop(message.port)
                if message.return_code == b'RFR':
                    ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x01' + b' '))
            elif message.m_type == b'SND_MOTOR_COMMAND':
                ret_msg: Message = Message(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x02' + b' '))

            connectedDevices[message.port][1].write(ret_msg.payload)
            await connectedDevices[message.port][1].drain()
            print(f"SENT [{ret_msg.return_code.decode()}]: {ret_msg.payload} to {addr}")
        except ConnectionResetError:
            print(f'CLIENTS DISCONNECTED...')
            connectedDevices.clear()
            break
            

async def main():
    server = await asyncio.start_server(
        listen_clients, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'[{addr[0]}:{addr[1]}]-[MSG]: SERVER RUNNING...')
    
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    loop.run_forever()
