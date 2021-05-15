# coding=utf-8

import asyncio



async def coro(i: int = 0):
    result = [i] * i
    return result


async def main(loopy):

    t = await asyncio.wait_for(coro(1000), timeout=None)
    print(f"RESULT IS {t}")

if __name__ == '__main__':
    loopy = asyncio.get_event_loop()
    asyncio.run(main(loopy=loopy))
    loopy.run_forever()
    print(f"LALLES {3*4}")
