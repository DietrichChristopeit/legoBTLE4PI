import asyncio
from asyncio import Event
from typing import Awaitable


class TestBind:

    def __init__(self):
        return


    async def keyEVT(self):


    def bind(self, event:Event, handler: Awaitable):


async def print_msg(text: str = None):
    if text is not None:
        print(text)
        print('sleeping(5)')
        for _ in range(0, 5):
            await asyncio.sleep(1.)
            print(f"slept {_}")
        print("Woke up")

    return


async def do_when(c):
    task = asyncio.create_task(print_msg(c))
    await asyncio.wait_for(task, 10.)
    return


async def something(on_key=None, on_when=None, what=None, when: int = 51):
    t = asyncio.create_task(on_key())
    for _ in range(0, 50):
        await asyncio.sleep(.1)
        print(f"{_}")
        if _ == when:
            if on_when is None:
                pass
            else:
                await on_when(what)
                print(f"Interrupted by {on_when.__repr__}")
            return

    print("Normal exit...")
    return


async def which_key_pressed():
    while True:
        if keyboard.Key is not None:
            pass
            #  print(keyboard.Key)
        await asyncio.sleep(0.01)


async def main():

    await something(on_key=which_key_pressed)

    return


if __name__ == '__main__':
    loopy = asyncio.get_event_loop()
    asyncio.run(main(), debug=True)
