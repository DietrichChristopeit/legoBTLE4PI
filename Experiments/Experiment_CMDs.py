# coding=utf-8
"""Experiment Example
Here some example action sequences are defined that the Lego(c) Model should perform.

It could be used as a template for other Experiments
"""
import asyncio
import time
from asyncio import sleep
from collections import defaultdict
from datetime import datetime


import numpy as np

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import C
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
                   debug=True, )
    RWD: SingleMotor = SingleMotor(name='RWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.B,
                                   gearRatio=2.67,
                                   wheel_diameter=100.0,
                                   debug=True, )
    STR: SingleMotor = SingleMotor(name='STR',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.C,
                                   gearRatio=1.00,
                                   debug=True, )
    FWD: SingleMotor = SingleMotor(name='FWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gearRatio=2.67,
                                   wheel_diameter=100.0,
                                   debug=True, )
    # ###################
    
    # Connect the devices with the Server and make them get notifications
    
    try:
        connectDevices = await asyncio.wait_for(e.setupConnectivity(devices=[HUB, STR, FWD, RWD]), timeout=20.0)
    except TimeoutError:
        print(f"{C.BOLD}{C.FAIL}SETUP TIMED OUT{C.ENDC}")
        return
    print(f"\t\t{C.BOLD}{C.UNDERLINE}{C.OKBLUE}****************DEVICE SETUP DONE****************{C.ENDC}\r\n")
    
    taskList: defaultdict = defaultdict(list)
    
    taskList['t0'] = [
            # {'cmd': RWD.GOTO_ABS_POS, 'kwargs': {'abs_pos': -400, 'abs_max_power': 100, 'speed': 50}},
            # {'cmd': RWD.GOTO_ABS_POS, 'kwargs': {'abs_pos': 200, 'abs_max_power': 100, 'speed': 50}},
            {'cmd': RWD.START_MOVE_DISTANCE, 'kwargs': {'distance': 1000.0, 'speed': 100, 'abs_max_power': 100}}
            ]
    
    result_t0 = await asyncio.wait_for(e.run(tasklist=taskList), timeout=None)
    
    while True:
        await sleep(.1)

    # 1. connect all devices to server; hub first
    # 2. issue issue GENERAL NOTIFICATION COMMAND REQ FROM HUB
    # 2.1. -> HUB ATTACHED IO's for ALL devices
    # 2.2 what to do with additional devices (need genaeral device maybe)
    # 3. issue Notification REQ from devices
    # --------------------------Setup done-----------------------
    # Motor commands


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
