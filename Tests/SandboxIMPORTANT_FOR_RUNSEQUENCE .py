import asyncio
import time
from asyncio import Event
from asyncio.futures import Future
from random import uniform


class C:
    
    def __init__(self, proceed: Event):
        self.proceed: Event = proceed
        pass
    
    async def do(self, t, ):
        await asyncio.sleep(t)
        self.proceed.set()
        return True
    
    def funct(self, p: int = 0):
        return p ** p
    
    async def CMD(self, cmd, result=None, args=None, wait: bool = False) -> Future:
        r = Future()
        
        # if proceed is None:
        #     proceed = Event()
        #     proceed.set()
        
        print(f"{cmd!r} \t\t\t\tWAITING AT GATE...")
        await self.proceed.wait()
        print(f"{cmd!r} \t\t\t\tstarting")
        if wait:
            self.proceed.clear()
            print(f"{cmd!r}: \t\t\t\tExecuting for 5.0 TO COMPLETE...")
            await self.do(5.0)
        else:
            t = uniform(.01, .9)
            print(f"{cmd!r}: \t\t\t\tExecuting {t} TO COMPLETE...")
            await asyncio.sleep(t)
        if result is None:
            r.set_result(True)
        else:
            print("ARGUMENTS: {}".format(self.funct(*args)))
            print(f"SET RESULT: {result(*args)}...")
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
    FWD = C(proceed=proceed)
    RWD = C(proceed=proceed)
    STR = C(proceed=proceed)
    CMD_SEQ0 = {
            'FWD': FWD.CMD('FORWARD_0'),
            'FWD0': FWD.CMD('FORWARD_WAIT0', wait=True),
            'RWD': RWD.CMD('REVERSE0', result=bool, args=(False,)),
            'Left': STR.CMD('LEFT0', result=STR.funct, args=(5,)),
            }
    n = 2.0
    print(f"SLEEPING {n}")
    time.sleep(n)
    print(f"WAKE UP NEO...")
    RESULTS0 = await CSEQ_run_until_complete(CMD_SEQ0)
    print(f"RESULT OF Sequence Item '{RESULTS0['Left'].result()}' of RESULTS0 is {RESULTS0['Left']}")
    if RESULTS0['Left'].result() == 3125:
        CMD_SEQ1 = {
                'RWD11': RWD.CMD('REVERSE_1.1'),
                'RIGHT11': STR.CMD('RIGHT_1.1'),
                'RIGHT12': STR.CMD('RIGHT_1.2'),
                'RWD12': RWD.CMD('REVERSE_1.2'),
                'RIGHT13': STR.CMD('RIGHT_1.3'),
                'RWD13': RWD.CMD('REVERSE_1.3'),
                'FWD11': FWD.CMD('FORWARD_WAIT1.1', wait=True),
                'RIGHT14': STR.CMD('RIGHT_1.4'),
                'RWD14': RWD.CMD('REVERSE_1.4'),
                }
        RESULTS1 = await CSEQ_run_until_complete(CMD_SEQ1)
        print(RESULTS1)
    CMD_SEQ2 = {
            'LEFT': STR.CMD('LEFT_2'),
            'FWD': FWD.CMD('FORWARD_2')
            }
    RESULTS2 = await CSEQ_run_until_complete(CMD_SEQ2)
    
    t_total_exec = time.monotonic() - t_exec_started
    print('====')
    print(f'Total Exec Time: {t_total_exec:.2f} seconds')


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    
    asyncio.run(main())
