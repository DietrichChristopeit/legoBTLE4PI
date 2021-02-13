import asyncio

from LegoBTLE.Device.messaging import Message

SEND_TO = {}
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888


async def handle_echo(reader, writer):
    global SEND_TO
    
    data = await reader.readuntil(b' ')
    message = Message(data)
    addr = writer.get_extra_info('peername')
    
    if (message.m_type == b'SERVER_ACTION') and (message.cmd == b'REG_W_SERVER') and (message.port not in
                                                                                      SEND_TO.keys()):
        print(f'[{SERVER_IP}:{SERVER_PORT}]-[RCV]: [{message.m_type.decode()}]-[{message.cmd.decode()}] = ['
              f'{message.return_code.decode()}]...')
        SEND_TO[message.port] = writer
        writer.write(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x01' + b' '))
        await writer.drain()
        print(f'[{SERVER_IP}:{SERVER_PORT}]-[MSG]: STORED CONNECTIONS = {SEND_TO}...')
        return
       
    print(f'[{SERVER_IP}:{SERVER_PORT}]-[RCV]: [{message.m_type.decode()}]-[{message.cmd.decode()}]...')
    print(f'[{SERVER_IP}:{SERVER_PORT}]-[SND]: [{message.m_type.decode()}]-[{message.cmd.decode()}] = [{message.payload}] '
          f'TO ['
          f'{message.port}]...')
    SEND_TO[message.port].write(message.payload)
    return


async def main():
    server = await asyncio.start_server(
        handle_echo, SERVER_IP, SERVER_PORT)
    
    addr = server.sockets[0].getsockname()
    
    print(server.sockets)
    print(f'[{SERVER_IP}:{SERVER_PORT}]-[MSG]: Server STARTED...')
    
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    
    asyncio.run(main())
