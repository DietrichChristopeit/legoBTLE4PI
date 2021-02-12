import asyncio
from random import uniform


async def send(item, q):
    print("STARTED SENDER")
    await asyncio.sleep(uniform(1.0, 5.0))
    await q.put(item)
    print(f'{item} sent')

    return


async def rec(q, terminate: asyncio.Event):
    print("Started REC")
    
    while True:
        if terminate.is_set():
            break
        await asyncio.sleep(.5, 1.0)
        item = await q.get()
        print(f'RECEIVED item {item}')
    await terminate.wait()
    print("REC: SHUTTING DOWN")
    return


async def main():
    q: asyncio.Queue = asyncio.Queue()
    t: asyncio.Event = asyncio.Event()
    for i in range(1, 10):
        asyncio.create_task(send(f'item {i}', q))
    asyncio.create_task(rec(q, t))
    print("MAIN: SLEEPING 30")
    await asyncio.sleep(30)
    print("MAIN: TERMINATE SET")
    t.set()
    # await asyncio.gather(sender, receiver)
    await asyncio.sleep(10)
    return


if __name__ == '__main__':
    asyncio.run(main())

