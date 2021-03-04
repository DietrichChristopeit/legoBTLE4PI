import asyncio
import time
from asyncio import Event
from asyncio.futures import Future
from random import uniform


async def do(t, e: Event = Event):
    await asyncio.sleep(t)
    e.set()
    return True


def funct(p: int = 0):
    return p**p


async def CMD(cmd, result=None, args=None, wait: bool = False, proceed: Event = Event) -> Future:
    r = Future()
    
    # if proceed is None:
    #     proceed = Event()
    #     proceed.set()
    
    print(f"{cmd!r} \t\t\t\tWAITING AT GATE...")
    await proceed.wait()
    print(f"{cmd!r} \t\t\t\tstarting")
    if wait:
        proceed.clear()
        print(f"{cmd!r}: \t\t\t\tExecuting for 5.0 TO COMPLETE...")
        await do(5.0, proceed)
    else:
        t = uniform(.01, .9)
        print(f"{cmd!r}: \t\t\t\tExecuting {t} TO COMPLETE...")
        await asyncio.sleep(t)
    if result is None:
        r.set_result(True)
    else:
        r.set_result(result(*args))
    print(f"{cmd!r}: \t\t\t\tEXEC COMPLETE...")
    return r


async def CSEQ_run_until_complete(run_sequence: [Future]) -> {}:
    run_sequence_values = (asyncio.create_task(v) for v in run_sequence.values())
    run_sequence_keys = list(run_sequence.keys())
    results = await asyncio.gather(*run_sequence_values)
    res = {k: results[run_sequence_keys.index(k)] for k in run_sequence_keys}
    return res


async def main():
    proceed: Event = Event()
    proceed.set()
    t_exec_started = time.monotonic()
    CMD_SEQ0 = {
            'FWD':  CMD('FORWARD_0', proceed=proceed),
            'FWD0': CMD('FORWARD_WAIT0', wait=True, proceed=proceed),
            'RWD': CMD('REVERSE0', result=bool, proceed=proceed, args=(False,)),
            'Left': CMD('LEFT0', result=funct, args=(5,), proceed=proceed),
            }
    n = 2.0
    print(f"SLEEPING {n}")
    time.sleep(n)
    print(f"WAKE UP NEO...")
    RESULTS0 = await CSEQ_run_until_complete(CMD_SEQ0)
    print(f"RESULT OF Sequence Item '{RESULTS0['Left'].result()}' of RESULTS0 is {RESULTS0['Left']}")
    if RESULTS0['Left'].result() == 3125:
        CMD_SEQ1 = {
                'RWD11':   CMD('REVERSE_1.1', proceed=proceed),
                'RIGHT11': CMD('RIGHT_1.1', proceed=proceed),
                'RIGHT12': CMD('RIGHT_1.2', proceed=proceed),
                'RWD12': CMD('REVERSE_1.2', proceed=proceed),
                'RIGHT13': CMD('RIGHT_1.3', proceed=proceed),
                'RWD13': CMD('REVERSE_1.3', proceed=proceed),
                'FWD11':  CMD('FORWARD_WAIT1.1', wait=True, proceed=proceed),
                'RIGHT14': CMD('RIGHT_1.4', proceed=proceed),
                'RWD14':   CMD('REVERSE_1.4', proceed=proceed),
                }
        RESULTS1 = await CSEQ_run_until_complete(CMD_SEQ1)
        print(RESULTS1)
    CMD_SEQ2 = {
            'LEFT': CMD('LEFT_2', proceed=proceed),
            'FWD':  CMD('FORWARD_2', proceed=proceed)
            }
    RESULTS2 = await CSEQ_run_until_complete(CMD_SEQ2)
    
    t_total_exec = time.monotonic() - t_exec_started
    print('====')
    print(f'Total Exec Time: {t_total_exec:.2f} seconds')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    asyncio.run(main())
