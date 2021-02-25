import asyncio
from random import uniform

cmd_completed = False


async def CMD_RECEIVE(x: str):
    global cmd_completed
    cmd_completed = False
    print(f"RECEIVED: {x}")
    # await asyncio.sleep(uniform(1.0, 5.0))
    cmd_completed = True
    return


async def CMD_RECEIVE1(x: str):
    global cmd_completed
    for i in range(1,10):
        cmd_completed = False
        print(f"RECEIVED: {x}{i}")
        await asyncio.sleep(uniform(1.0, 1.02))
        cmd_completed = True
    return


async def wait_completed() -> bool:
    while not cmd_completed:
        print("waiting")
        await asyncio.sleep(.001)
        pass
    return True


async def CMD_SEND(x: str, wait_comp: bool = False):
    l= asyncio.get_running_loop()
    t1 = asyncio.create_task(CMD_RECEIVE("LALLES0"))
    t2 = asyncio.create_task(CMD_RECEIVE1("LALLES1"))
    t3 = asyncio.create_task(CMD_RECEIVE1("LALLES........."))
    
    # await asyncio.wait((t1, t2, t3), return_when='ALL_COMPLETED')
    task = asyncio.create_task(wait_completed())
    X, y = await asyncio.wait((task, t1, t2, t3, ))
    if t1 in X:
        print("FINISHED T1")
    await CMD_RECEIVE("LALLES2")
    print("After Completion")
    await CMD_RECEIVE("LALLES3")
    return


if __name__ == '__main__':
    
    asyncio.run(CMD_SEND("LALLES", True))

