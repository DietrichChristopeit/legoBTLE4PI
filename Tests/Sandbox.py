import asyncio
import functools
import time
from asyncio import Future
from asyncio.exceptions import CancelledError
from random import uniform


def allDone(cmd):
    print(f"ALL IS DONE for {cmd}")
    return


async def CMD(cmd, result=None, wait: bool = False, args=(True,)) -> Future:
    r = Future()
    print(f"EXECUTING CMD: {cmd!r}")
    if wait:
        print(f"{cmd}:WAITING FOR EXEC COMPLETE...")
        for t in range(0, 5):
            time.sleep(1.0)
        
    else:
        dt = uniform(3.0, 3.0)
        print(f"{cmd}:WAITING {dt}...")
        await asyncio.sleep(dt)
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
    t_exec_started = time.monotonic()
    CMD_SEQ0 = {'FWD': CMD('FORWARD'),
                'RWD': CMD('REVERSE', result=bool, args=(False,)),
                'Left': CMD('LEFT', result=str, args=('LALLES',)),
                'FWD0': CMD('FORWARD_0', wait=True)
                }
    print(f"SLEEPING 20")
    time.sleep(20.0)
    print(f"WAKE UP NEO...")
    RESULTS0 = await CSEQ_run_until_complete(CMD_SEQ0)
    
    if RESULTS0['Left'].result() == 'LALLES':
        CMD_SEQ1 = {'RWD': asyncio.ensure_future(CMD('REVERSE')),
                    'RIGHT': asyncio.ensure_future(CMD('RIGHT')),
                    'FWD1': asyncio.ensure_future(CMD('FORWARD_1', wait=True)),
                    }
        RESULTS1 = await CSEQ_run_until_complete(CMD_SEQ1)
        
    CMD_SEQ2 = {'LEFT': asyncio.ensure_future(CMD('LEFT')),
                'FWD': asyncio.ensure_future(CMD('FORWARD'))
                }
    RESULTS2 = await CSEQ_run_until_complete(CMD_SEQ2)
        
    t_total_exec = time.monotonic() - t_exec_started
    print('====')
    print(f'Total Exec Time: {t_total_exec:.2f} seconds')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    asyncio.run(main())
