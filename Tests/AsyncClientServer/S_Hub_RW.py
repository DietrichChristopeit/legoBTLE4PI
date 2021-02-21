import asyncio
import sys
from asyncio import AbstractServer, StreamReader, StreamWriter

try:
    import bluepy
    import bluepy.btle
    import bluepy.btle.BTLEInternalError
except ImportError:
    print(f"NO bluepy on WINDOWS")

from LegoBTLE.Device.old.messaging import Message

SEND_TO = {}
_host = '127.0.0.1'
SERVER_PORT = 8888


class MessageHandlingServer:
    
    def __init__(self, name: str = "LegoHub", host: str = '127.0.0.1', port: int = 8888,
                 btledevice: str = '90:84:2B:5E:CF:1F',
                 debug=False):
        
        self._name = name
        self._host = host
        self._port = port
        self._active_connections = {}
        self._debug = debug
        self._A_BTLE = btledevice
        self._dev: btle.Peripheral = None
        self._handling_server: AbstractServer
        return
    
    async def start(self):
        if self._debug:
            print(f"[{self._host}:{self._port}]-[MSG]: COMMENCE [SERVER_START]...")
        server = await asyncio.start_server(self.handle_communication, self._host, self._port)
        await server.serve_forever()
        return
    
    async def handle_communication(self, reader: StreamReader, writer: StreamWriter):
        
        message = Message(await reader.readuntil(b' '))
        print(f"RECEIVED: {message.payload}")
        
        if (message.m_type == b'SND_SERVER_ACTION') and \
                (message.cmd == b'REG_W_SERVER') and \
                (message.port not in self._active_connections.keys()):
            
            print(f'[{self._host}:{self._port}]-[RCV]: [{message.m_type.decode()}]-[{message.cmd.decode()}] = ['
                  f'{message.return_code.decode()}]...')
            self._active_connections[message.port] = writer
            self._active_connections[message.port].write(bytearray(b'\x07\x00\x00' + message.port + b'\x00\x01' + b' '))
            await self._active_connections[message.port].drain()
            print(f'[{self._host}:{self._port}]-[MSG]: STORED CONNECTIONS = {self._active_connections}...')
        
        elif message.m_type.startswith(b'RCV_'):
            print(f'[{self._host}:{self._port}]-[RCV]: [{message.m_type.decode()}]-[{message.cmd.decode()}]...')
            print(
                f'[{self._host}:{self._port}]-[SND]: [{message.m_type.decode()}]-[{message.cmd.decode()}] = ['
                f'{message.payload}] '
                f'TO ['
                f'{message.port}]...')
            self._active_connections[message.port].write(message.payload)
            await self._active_connections[message.port].writer.drain()
        
        elif message.m_type.startswith(b'SND_'):
            if sys.platform == 'win32':
                print(f"[{self._host}:{self._port}]-[MSG]: [ECHOING] = [{message.payload}]...")
                # self._active_connections[message.port].\
                self._active_connections[message.port].write(message.payload)
                # await self._active_connections[message.port].drain()
                await self._active_connections[message.port].drain()
            
            print(f"[{self._host}:{self._port}]-[MSG]: [SEND_MESSAGE_TO_BTLE]...")
            # self._dev.write(...)
            # continue
    
    async def connect_btle(self) -> bool:
        print(f"[{self._host}:{self._port}]-[MSG]: COMMENCE [CONNECTING] --> [{self._A_BTLE}]")
        self._dev = btle.Periperal(self._A_BTLE)
        print(f"[{self._host}:{self._port}]-[MSG]: [CONNECTING] DONE --> [{self._A_BTLE}]")
        return True
    

async def main():
    S_CMD_HANDLING = MessageHandlingServer(host='127.0.0.1', port=8888)
    
    T_SERVER = asyncio.create_task(S_CMD_HANDLING.start(), name="CMD_HANDLING_SERVER")
    # T_BTLE = asyncio.create_task(S_CMD_HANDLING.connect_btle(), name="BTLE_DEVICE")
    dones, pendings = await asyncio.wait((T_SERVER, ))
    print(f'[{T_SERVER.result().sockets[0].getsockname()[0]}:{T_SERVER.result().sockets[0].getsockname()[1]}]-[MSG]: '
          f'Server STARTED...')
    async with T_SERVER.result():
        await T_SERVER.result().serve_forever()
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # asyncio.(main())
    asyncio.run_coroutine_threadsafe(main(), loop)
    loop.run_forever()