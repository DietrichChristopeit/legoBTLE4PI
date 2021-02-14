import asyncio
import socket
from asyncio.streams import StreamReader, StreamWriter

from LegoBTLE.Device.messaging import Message


async def connectTo(hubAdr: str = '127.0.0.1', hubPort: int = 8888) -> (StreamReader, StreamWriter):
    receiver, sender = await asyncio.open_connection(hubAdr, hubPort)
    return receiver, sender


class Motor:
    
    def __init__(self, name: str = 'Motor', motorPort=b'', rdr: StreamReader = None, wrtr: StreamWriter = None,
                 shutdown: asyncio.Event = None):
        self._name: str = name
        self._motorPort: bytes = motorPort
        self._CMD_RECEIVER = rdr
        self._CMD_SENDER = wrtr

        self._E_SHUTDOWN: asyncio.Event = shutdown
        return

    @property
    def CMD_RECEIVER(self) -> StreamReader:
        return self._CMD_RECEIVER

    @CMD_RECEIVER.setter
    def CMD_RECEIVER(self, s: StreamReader):
        self._CMD_RECEIVER = s
        return

    async def startup(self):
        
        # send identifier
        ack: bytearray = bytearray(b'\x0f\x00\x04' + self._motorPort + b'\x01\x2f\x00\x00\x10\x00\x00\x00\x10\x00\x00')
        ack.extend(b' ')
        await asyncio.sleep(5.0)
        print(f'START COMPLETE')
        # #######
        self._CMD_SENDER.write(ack)
        return True
    
    async def CMD_READ(self):
        while not self._E_SHUTDOWN.is_set():
            data: bytes = await self._CMD_RECEIVER.readuntil(b' ')
            print(f'DATA READ: {data[0:data[0] - 1]}')
            RCV_RESULT = Message(data[0:data[0]-1])
            
            print(f'[{RCV_RESULT.port.hex()}]:[{self._name}]-[RCV]: [{RCV_RESULT.m_type}]...')
        print(f'[{self._name}]-[RCV]: [SHUTDOWN]: SHUTTING DOWN...')
        return await self.C_SHUTDOWN()
    
    async def CMD_SEND(self, cmd: Message) -> bool:
        payload = bytearray(cmd.payload)
        
        payload.extend(b' ')
        print(f'[{self._motorPort}]:[{self._name}]-[SND]: [{cmd.m_type}] SENT = [{cmd.payload}]...')
        self._CMD_SENDER.write(payload)
        return True
    
    async def C_SHUTDOWN(self) -> bool:
        self._CMD_SENDER.close()
        print(f'[{self._motorPort}]:[{self._name}]-[MSG]: CONNECTION CLOSED TO HUB...')
        return True

    
async def main():
    e = asyncio.Event()
    # asyncio.run_coroutine_threadsafe(SERVER_TCP.main(), asyncio.get_running_loop())
    # c1 = RCV_MSG('motor1', e)
    s1 = await connectTo()
    m1 = Motor(motorPort=b'\x00', name="Vorderradantrieb", shutdown=e, rdr=s1[0], wrtr=s1[1])
    s2 = await connectTo()
    m2 = Motor(motorPort=b'\x01', name="Hinterradantrieb", shutdown=e, rdr=s2[0], wrtr=s2[1])
    await asyncio.create_task(m1.startup())
    await asyncio.create_task(m2.startup())
    await asyncio.create_task(m1.CMD_READ())
    await asyncio.create_task(m2.CMD_READ())
    m1m = bytearray(b'\x00\x81\x02\x02\x01\xff\xff')
    m1ms = bytearray(len(m1m).to_bytes(1, 'little')) + m1m
    m2m = bytearray(b'\x00\x47\x01\x01\x01\xff\xff')
    m2ms = bytearray(len(m1m).to_bytes(1, 'little')) + m2m
    await asyncio.create_task(m1.CMD_SEND(Message(m1ms)))
    await asyncio.create_task(m2.CMD_SEND(Message(m2ms)))
    return True

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    # loop.run_until_complete(main())
    loop.run_forever()
    loop.close()
