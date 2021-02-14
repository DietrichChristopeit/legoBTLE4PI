import asyncio
import socket


class MyProtocol(asyncio.Protocol):
    
    def __init__(self, on_con_lost):
        self.transport = None
        self.on_con_lost = on_con_lost
    
    def connection_made(self, transport):
        self.transport = transport
    
    def data_received(self, data):
        print("Received:", data.decode())
        
        # We are done: close the transport;
        # connection_lost() will be called automatically.
        self.transport.close()
    
    def connection_lost(self, exc):
        # The socket has been closed
        self.on_con_lost.set_result(True)



async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    
    # Create a pair of connected sockets
    rsock, wsock = socket.socketpair()
    
    # Register the socket to wait for data.
    transport, protocol = await loop.create_connection(
        lambda: MyProtocol(on_con_lost), sock=rsock)
    
    # Simulate the reception of data from the network.
    loop.call_soon(wsock.send, 'abc'.encode())
    
    try:
        await protocol.on_con_lost
    finally:
        transport.close()
        wsock.close()
if __name__ == '__main__':
    asyncio.run(main())