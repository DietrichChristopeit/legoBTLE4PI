# coding=utf-8
"""Experiment Example
Here some example action sequences are defined that the Lego(c) Model should perform.

It could be used as a template for other Experiments
"""
import asyncio
import time
from asyncio import sleep
from datetime import datetime

import numpy as np

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT, PORT, SI
from LegoBTLE.User.executor import Experiment


async def main():
    """Main function to define an run an Experiment in.

    This function should be the sole entry point for using the whole
    project.
    
    Here some examples are shown as how to operate the motors.
    
    Examples:
    ---------
    Hub/Motor Definition and Initialization:
    
    >>> HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888), debug=True)
    >>> RWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888),
                                       port=PORT.B, # also b'\\x01' or 1 is accepted
                                       name='REAR WHEEL DRIVE',
                                       gearRatio=2.67,
                                       debug=True)
                                       
    Turn the ``RWD`` Motor for some time in milliseconds (ms) in one direction and after completion immediately in the opposite direction:
    
    >>> task = [{'cmd': RWD.START_SPEED_TIME,
                 'kwargs': {'time': 10000,
                            'speed': 100, # the sign (here +) defines the the direction
                            'power': 100,
                            'on_completion': MOVEMENT.COAST,
                            'use_profile': 1, # see example for acceleration and deceleration profiles
                            'delay_before': 0.0,
                            'delay_after': 0.0,
                           },
                 'task': {'tp_id': 'RWD_RUN_TIME_FORWARD', } # the tp_id (the name of the task) can be anything,
                                                             # by this name the results can be retrieved
                },
                {'cmd': RWD.START_SPEED_TIME,
                 'kwargs': {'time': 10000,
                            'speed': -100, # the sign (here -) defines the the direction
                            'power': 100,
                            'on_completion': MOVEMENT.COAST,
                            'use_profile': 1, #see example for acceleration and deceleration profiles
                            'delay_before': 0.0,
                            'delay_after': 0.0,
                           },
                 'task': {'tp_id': 'RWD_RUN_TIME_REVERSE', } # the tp_id (the name of the task) can be anything
                                                             # by this name the results can be retrieved
                },
               ]
    With debug on: lots of info arrives
    
    Returns:
    -------
    None :
        None.

    """
    # time.sleep(5.0) # for video, to have time to fumble with the
    # phone keys :-)
    # time.sleep(5.0)
    
    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0',
                               measure_time=False,
                               loop=loopy,
                               debug=True,
                               )
    # Device definitions
    HUB: Hub = Hub(name='LEGO HUB 2.0',
                   server=('127.0.0.1', 8888),
                   debug=True,)
    RWD: SingleMotor = SingleMotor(name='RWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.B,
                                   gearRatio=2.67,
                                   debug=True,)
    STR: SingleMotor = SingleMotor(name='STR',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.C,
                                   gearRatio=1.00,
                                   debug=True,)
    FWD: SingleMotor = SingleMotor(name='FWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gearRatio=2.67,
                                   debug=True,)
    # ###################
    
    # Connect the devices with the Server and make them get notifications
    t1 = await asyncio.wait_for(e.setupNotifyConnect([HUB, FWD, STR, RWD]).run(),
                                loop=loopy,
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
    
    # t0 = await asyncio.wait_for(e.run(
    # experimentActions_USE_ACC_DEACC_PROFILE, loop=loopy),
    # timeout=None)
    
    x: float = 0.0
    tsin: [] = []
    currentAngle = RWD.current_angle(si=SI.DEG)
    
    t_reset = [{'cmd': RWD.SET_POSITION,
                'kwargs': {'pos': 0, },
                'task': {'tp_id': 'RWD_RESET', }
                }
               ]
    
    # async for i in sinGenerator(start=0.0,
    #                             end=180,
    #                             step=5.0,
    #                             inSI=SI.DEG):
    #     tsin += [{'cmd': RWD.GOTO_ABS_POS,
    #               'kwargs': {'abs_pos': int(abs(round(i[0]*1000/RWD.gearRatio))),
    #                          'speed': 100,
    #                          'abs_max_power': 100,
    #                          'on_completion': MOVEMENT.COAST,
    #                          'use_profile': 3,
    #                          'delay_after': 0.01
    #                          },
    #               'task': {'tp_id': f'RWD_sin{i[1]}', }
    #               }]
    #
    t_r = await asyncio.wait_for(e.runnable_tasks(t_reset).run(),
                                 timeout=None)
    
    amplitude = 90
    start = time.clock_gettime(time.CLOCK_MONOTONIC)
    print(f"CURRENT ANGLE: {RWD.current_angle(si=SI.DEG)}")
    for i in range(1, 200):
        
        tsin_new = [{'cmd': RWD.GOTO_ABS_POS,
                     'kwargs': {'abs_pos': int(
                         round(np.sin(round(time.clock_gettime(time.CLOCK_MONOTONIC) - start) * 10) * amplitude)),
                                'speed': 100,
                                'abs_max_power': 100,
                                'on_completion': MOVEMENT.COAST,
                                'use_profile': 3,
                                }, 'task': {'tp_id': f'RWD_sin{i}', }
                     }]
        
        t0 = await asyncio.wait_for(e.runnable_tasks(tsin_new).run(),
                                    timeout=None)
        time.sleep(1.0)
    print("DONE WITH IT...")
    while True:
        print(f"CURRENT ANGLE AT END: {RWD.current_angle(si=SI.DEG)}")
        await sleep(.1)


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
