import asyncio


async def p0(n: int) -> str:
    await asyncio.sleep(n)
    print(f"READY P0")
    return 'p0'


async def p1(n: int, arg: str) -> str:
    print(f"sleeping after p0 has ended")
    print(f"RESULT: {arg}")
    await asyncio.sleep(n)
    return 'p1'


async def chain(n: int) -> bool:
    result = await p0(2)
    await p1(n, result)

    return True

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(chain(3))
