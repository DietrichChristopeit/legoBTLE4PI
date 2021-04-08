# coding=utf-8
"""Experiment Example
Here some example action sequences are defined that the Lego(c) Model should perform.

It could be used as a template for other Experiments
"""
import logging
from colorlog import ColoredFormatter
import asyncio
from collections import defaultdict
from datetime import datetime

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.types import C
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.LegoWP.types import PORT
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
                            'speed': 100, # the _sign (here +) defines the the direction
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
                            'speed': -100, # the _sign (here -) defines the the direction
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
    LOG_LEVEL = logging.DEBUG
    LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log = logging.getLogger('Experiment.Experiment_Cmds')
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)

# time.sleep(5.0) # for video, to have time to fumble with the phone keys :-)
    
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
                                   forward=MOVEMENT.REVERSE,
                                   wheel_diameter=100.0,
                                   debug=True, )
    
    STR: SingleMotor = SingleMotor(name='STR',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.C,
                                   gearRatio=1.00,
                                   clockwise=MOVEMENT.COUNTERCLOCKWISE,
                                   debug=True, )
    
    FWD: SingleMotor = SingleMotor(name='FWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gearRatio=2.67,
                                   wheel_diameter=100.0,
                                   forward=MOVEMENT.REVERSE,
                                   debug=True,
                                   )
    
    FWD_RWD: SynchronizedMotor = SynchronizedMotor(name='FWD_RWD_SYNC',
                                                   motor_a=FWD,
                                                   motor_b=RWD,
                                                   server=('127.0.0.1', 8888),
                                                   forward=MOVEMENT.FORWARD,
                                                   debug=True,
                                                   )
    # ###################
    
    # Connect the devices with the Server and make them get notifications
    
    try:
        connectDevices = await e.setupConnectivity(devices=[HUB, STR, FWD, RWD, FWD_RWD])
    except TimeoutError:
        print(f"{C.BOLD}{C.FAIL}SETUP TIMED OUT{C.ENDC}\r\n"
              f"CONNECTED DEVICES: ")
        return
    print(f"\t\t{C.BOLD}{C.UNDERLINE}{C.OKBLUE}****************DEVICE SETUP DONE****************{C.ENDC}\r\n")
    
    taskList: defaultdict = defaultdict(list)
    
    taskList['t0'] = [
            # {'cmd': RWD.GOTO_ABS_POS, 'kwargs': {'position': -400, 'abs_max_power': 100, 'speed': 50}},
            # {'cmd': RWD.GOTO_ABS_POS, 'kwargs': {'position': 200, 'abs_max_power': 100, 'speed': 50}},
            # {'cmd': RWD.START_MOVE_DISTANCE, 'kwargs': {'distance': 1500.0, 'speed': 100, 'abs_max_power': 100, }},
            # {'cmd': FWD_RWD.GOTO_ABS_POS_SYNCED, 'kwargs': {'abs_pos_a': 1000, 'abs_pos_b': 1000, 'speed': 60, 'abs_max_power': 90}},
            # {'cmd': FWD_RWD.GOTO_ABS_POS_SYNCED, 'kwargs': {'abs_pos_a': -1000, 'abs_pos_b': -1000, 'speed': 100, 'abs_max_power': 100}},
            {'cmd': FWD_RWD.START_SPEED_TIME, 'kwargs': {'time': 5000, 'speed': 80, 'power': 100}},
            # {'cmd': RWD.START_SPEED_TIME, 'kwargs': {'time': 5000, 'speed': -100, 'power': 100}},
            {'cmd': FWD_RWD.START_SPEED_TIME, 'kwargs': {'time': 5000, 'speed': 100, 'power': 100}},
            
            ]
    
    result_t0 = await asyncio.wait_for(e.run(tasklist=taskList), timeout=None)
    
    while True:
        await asyncio.sleep(.0001)
    
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
