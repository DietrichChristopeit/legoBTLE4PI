# coding=utf-8 ************************************************************************************************** MIT
# License * * Copyright (c) 2021 Dietrich Christopeit * * Permission is hereby granted, free of charge, to any person
# obtaining a copy                    * of this software and associated documentation files (the "Software"),
# to deal                   * in the Software without restriction, including without limitation the rights
# * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       * copies of the
# Software, and to permit persons to whom the Software is                           * furnished to do so, subject to
# the following conditions: * * The above copyright notice and this permission notice shall be included in all
# * copies or substantial portions of the Software. * * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR                      * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     * AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          * LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   * OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE                   * SOFTWARE. *
# **************************************************************************************************

import asyncio
import time
from asyncio import sleep
from datetime import datetime

import numpy as np

from Experiments.generators import connectAndSetNotify
from Experiments.generators import sinGenerator
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.LegoWP.types import SI
from LegoBTLE.User.executor import Experiment


async def main():
    """Main function to define an run an Experiment in.

    This function should be the sole entry point for using the whole
    project.
    
    :returns: None
    :rtype: None

    """
    # time.sleep(5.0) # for video, to have time to fumble with the
    # phone keys :-)
    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0',
                               measure_time=False,
                               debug=True)
    
    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888),
                   debug=True)
    RWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888),
                                   port=b'\x01', name='RWD',
                                   gearRatio=2.67, debug=True)
    STR: SingleMotor = SingleMotor(server=('127.0.0.1', 8888),
                                   port=b'\x02', name='STR',
                                   gearRatio=1.00, debug=True)
    FWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888),
                                   port=b'\x00', name='FWD',
                                   gearRatio=2.67, debug=True)
    
    t1 = await asyncio.wait_for(e.createAndRun(connectAndSetNotify([HUB,
                                                                    FWD,
                                                                    STR,
                                                                    RWD, ]),
                                               loop=loopy),
                                timeout=None)
    await sleep(3)
    experimentActions_USE_ACC_DEACC_PROFILE = [
            
            {'cmd': RWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 2000, 'profile_nr': 1, },
             'task': {'tp_id': 'HUB_ACC_PROFILE', }
             },
            {'cmd': RWD.SET_DEACC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 300, 'profile_nr': 1, },
             'task': {'tp_id': 'HUB_DEACC_PROFILE', }
             },
            {'cmd': FWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 20, 'profile_nr': 2, },
             'task': {'tp_id': 'HUB_FWD_ACC_PROFILE', }
             },
            {'cmd': FWD.SET_DEACC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 3000, 'profile_nr': 2, },
             'task': {'tp_id': 'HUB_FWD_DEACC_PROFILE', }
             },
            {'cmd': RWD.SET_ACC_PROFILE,
             'kwargs': {'ms_to_full_speed': 2, 'profile_nr': 3, },
             'task': {'tp_id': 'HUB_ACC_PROFILE', }
             },
            {'cmd': RWD.SET_DEACC_PROFILE,
             'kwargs': {'ms_to_zero_speed': 250, 'profile_nr': 3, },
             'task': {'tp_id': 'HUB_DEACC_PROFILE', }
             },
            
            {'cmd': RWD.START_SPEED_TIME,
             'kwargs': {'time': 10000,
                        'speed': 100,
                        'power': 100,
                        'on_completion': MOVEMENT.COAST,
                        'use_profile': 1,
                        'delay_before': 0.0,
                        'delay_after': 0.0,
                        },
             'task': {'tp_id': 'RWD_GOTO', }
             },
            {'cmd': RWD.START_SPEED_TIME,
             'kwargs': {'time': 10000,
                        'speed': -100,
                        'power': 100,
                        'on_completion': MOVEMENT.COAST,
                        'use_profile': 1,
                        'delay_before': 0.0,
                        'delay_after': 0.0,
                        },
             'task': {'tp_id': 'RWD_GOTO1', }
             },
            
            {'cmd': RWD.START_MOVE_DEGREES,
             'kwargs': {
                     'use_profile': 2,
                     'on_completion': MOVEMENT.HOLD,
                     'degrees': 360,
                     'delay_before': 3.0,
                     'speed': 100,
                     'abs_max_power': 100
                     },
             'task': {'tp_id': 'RWD_DEG1', }
             },
            
            # {'cmd': FWD.START_SPEED_TIME,
            #  'kwargs': {'time': 10000,
            #             'speed': 100,
            #             'power': 100,
            #             'on_completion': MOVEMENT.BREAK,
            #             'use_profile': 2,
            #             'delay_before': 0.0,
            #             'delay_after': 0.0,
            #             },
            #  'task': {'tp_id': 'FWD_GOTO', }},
            # {'cmd': FWD.START_SPEED_TIME,
            #  'kwargs': {'time': 10000,
            #             'speed': -20,
            #             'power': 100,
            #             'on_completion': MOVEMENT.BREAK,
            #             'use_profile': 2,
            #             'delay_before': 0.0,
            #             'delay_after': 0.0,
            #             },
            #  'task': {'tp_id': 'FWD_GOTO1', }},
            
            ]
    
    # tsin = [{'cmd': RWD.GOTO_ABS_POS, 'kwargs': {'abs_pos': y,
    # 'abs_max_power': 80}, 'task': {'tp_id': 'RWD_sin', }} async for
    # y in createGenerator()]
    
    # t0 = await asyncio.wait_for(e.createAndRun(
    # experimentActions_USE_ACC_DEACC_PROFILE, loop=loopy),
    # timeout=None)
    
    x: float = 0.0
    tsin: [] = []
    async for i in sinGenerator(start=0.0,
                                end=180,
                                step=5.0,
                                inSI=SI.DEG):
        tsin += [{'cmd': RWD.GOTO_ABS_POS,
                  'kwargs': {'abs_pos': int(abs(round(i[0]*1000/RWD.gearRatio))),
                             'speed': 100,
                             'abs_max_power': 100,
                             'on_completion': MOVEMENT.COAST,
                             'use_profile': 3,
                             'delay_after': 0.01
                             }, 'task': {'tp_id': f'RWD_sin{i[1]}', }
                  }]
    
    amplitude = 105
    seconds = datetime.now().second
    for i in range(1, 20):
        
        tsin_new = [{'cmd': RWD.GOTO_ABS_POS,
                 'kwargs': {'abs_pos': int(round(np.sin(seconds)*amplitude)),
                            'speed': 70,
                            'abs_max_power': 100,
                            'on_completion': MOVEMENT.COAST,
                            'use_profile': 3,
                            'delay_after': 0.01
                            }, 'task': {'tp_id': f'RWD_sin{i}', }
                 }]
        t0 = await asyncio.wait_for(e.createAndRun(tsin_new,
                                                   loop=loopy),
                                    timeout=None)
        time.sleep(.9)
        seconds = datetime.now().second
   
    print("DONE WITH IT...")


if __name__ == '__main__':
    """This is the loading programme.
    
    It can be but is not intended to be modified.
    
    Nothing really special here.
    
    """
    loopy = asyncio.get_event_loop()
    
    t0 = datetime.timestamp(datetime.now())
    asyncio.run(main())
    loopy.run_forever()
    print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
