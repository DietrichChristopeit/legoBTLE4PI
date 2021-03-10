# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
import asyncio
import time
from asyncio import AbstractEventLoop, Event, Future
from random import uniform

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT


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


async def run_experiment(run_sequence: [Future]) -> {}:
    run_sequence_values = [asyncio.create_task(v) for v in run_sequence.values()]
    run_sequence_keys = list(run_sequence.keys())
    results = await asyncio.gather(*run_sequence_values)
    res = {k: results[run_sequence_keys.index(k)] for k in run_sequence_keys}
    print(res)
    return {}


def unpackResults(**results) -> list:
    print(results)
    return results


async def main(loop: AbstractEventLoop):
    proceed: Event = Event()
    proceed.set()
    t_exec_started = time.monotonic()
    
    HUB: Hub = Hub(name="Lego Hub 2.0", server=('127.0.0.1', 8888), exec_adv=proceed)
    
    FWD: SingleMotor = SingleMotor(name="FWD", port=b'\x02', gearRatio=2.67, server=('127.0.0.1', 8888),
                                   exec_adv=proceed)
    RWD: SingleMotor = SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67, server=('127.0.0.1', 8888),
                                   exec_adv=proceed)
    STR: SingleMotor = SingleMotor(name="STR", port=b'\x00', server=('127.0.0.1', 8888),
                                   exec_adv=proceed)
    
    CONNECT_SEQ = {'CNCT_HUB': HUB.connect_srv(wait=False),
                   'CNCT_STR': STR.connect_srv(wait=False),
                   'CNCT_RWD': RWD.connect_srv(wait=False),
                   'CNCT_FWD': FWD.connect_srv(wait=True),
                   'MOV_STR0': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                            abs_max_power=100, wait=True),
                   'MOV_RWD1': RWD.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=True),
                   'MOV_STR1': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=True),
                   'MOV_STR3': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=True),
                   'MOV_FWD0': FWD.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=True),
                   'MOV_STR4': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=True),
                   'MOV_STR5': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                      abs_max_power=100, wait=False),
                   'MOV_STR6': STR.START_MOVE_DEGREES(on_completion=MOVEMENT.HOLD, degrees=90, speed=-100,
                                                            abs_max_power=100, wait=False)
                   }  # {'CNCT_HUB': HUB.connect_srv(wait=True),
    #  'CNCT_FWD': FWD.connect_srv(),
    #  'CNCT_RWD': RWD.connect_srv(),
   
    print(f"start in 3")
    time.sleep(3.0)
    RESULTS0 = await run_experiment(CONNECT_SEQ)
    print(f"{asyncio.all_tasks()}")
    for r in RESULTS0:
        print(f"{r}: {RESULTS0[r]}")
        
    # for r in RESULTS0:
    #   print(f"GOT RESULTS:\r\n{RESULTS0[r]}")


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    
    asyncio.run(main(loop=loop))
    
    loop.run_forever()
