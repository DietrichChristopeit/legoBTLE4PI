import asyncio
import time
from asyncio import Event
from asyncio.futures import Future
from random import uniform


async def do(t, e: Event):
    await asyncio.sleep(t)
    e.set()
    return True


async def CMD(cmd, result=None, args=None, wait: bool = False, proceed: Event = None) -> Future:
    r = Future()
    print(f"EXECUTING CMD: {cmd!r}")
    if proceed is None:
        proceed = Event()
        proceed.set()
        
    await proceed.wait()
    if wait:
        proceed.clear()
        print(f"{cmd}: WAITING 5.0 FOR EXEC COMPLETE...")
        await do(5.0, proceed)
    else:
        t = uniform(.01, .09)
        print(f"{cmd}: WAITING {t} FOR EXEC COMPLETE...")
        await asyncio.sleep(t)
    if result is None:
        r.set_result(True)
    else:
        r.set_result(result(*args))
    print(f"{cmd}: EXEC COMPLETE...")
    return r


async def CSEQ_run_until_complete(run_sequence: [Future]) -> {}:
    run_sequence_values = (asyncio.ensure_future(v) for v in run_sequence.values())
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
            'Left': CMD('LEFT0', result=str, proceed=proceed, args=('LALLES',)),
            }
    n = 2.0
    print(f"SLEEPING {n}")
    time.sleep(n)
    print(f"WAKE UP NEO...")
    RESULTS0 = await CSEQ_run_until_complete(CMD_SEQ0)
    
    if RESULTS0['Left'].result() == 'LALLES':
        CMD_SEQ1 = {
                'RWD':   CMD('REVERSE_1', proceed=proceed),
                'RIGHT': CMD('RIGHT_1', proceed=proceed),
                'FWD1':  CMD('FORWARD_WAIT1', wait=True, proceed=proceed),
                }
        RESULTS1 = await CSEQ_run_until_complete(CMD_SEQ1)
    
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
