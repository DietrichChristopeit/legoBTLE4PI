import asyncio
from random import uniform


async def factorial(name, number) -> int:
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({i})...")
        await asyncio.sleep(uniform(1.0, 2.0))
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")
    return f


def taskGen():
    t = [factorial("A", 2),
         factorial("B", 3),
         factorial("C", 4),
         ]
    return t


async def main():
    # Schedule three calls *concurrently*:
    result = await asyncio.gather(*taskGen())
    print(result)


if __name__ == '__main__':
    
    asyncio.run(main())
