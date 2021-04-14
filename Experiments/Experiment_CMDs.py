# coding=utf-8
"""Experiment Example
Here some example action sequences are defined that the Lego(c) Model should perform.

It could be used as a template for other Experiments
"""
import logging

import numpy as np
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
from LegoBTLE.networking.prettyprint.debug import debug_info


async def main():
    """Main function to define an run_each an Experiment in.

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
                               debug=False,
                               )
    # Device definitions
    HUB: Hub = Hub(name='LEGO HUB 2.0',
                   server=('127.0.0.1', 8888),
                   debug=False, )
    
    RWD: SingleMotor = SingleMotor(name='RWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.B,
                                   gearRatio=2.67,
                                   clockwise=MOVEMENT.COUNTERCLOCKWISE,
                                   wheel_diameter=100.0,
                                   debug=False, )
    
    STR: SingleMotor = SingleMotor(name=f"{C.HEADER}STEERING MOTOR{C.ENDC}",
                                   server=('127.0.0.1', 8888),
                                   port=PORT.C,
                                   gearRatio=1.0,
                                   time_to_stalled=0.4,
                                   stall_bias=0.2,
                                   clockwise=MOVEMENT.CLOCKWISE,
                                   debug=True, )
    
    FWD: SingleMotor = SingleMotor(name='FWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gearRatio=2.67,
                                   wheel_diameter=100.0,
                                   clockwise=MOVEMENT.COUNTERCLOCKWISE,
                                   debug=False,
                                   )
    
    # FWD_RWD: SynchronizedMotor = SynchronizedMotor(name='FWD_RWD_SYNC',
    #                                                motor_a=FWD,
    #                                                motor_b=RWD,
    #                                                server=('127.0.0.1', 8888),
    #                                                clockwise=MOVEMENT.CLOCKWISE,
    #                                                debug=True,
    #                                                )
    # ###################
    
    # Connect the devices with the Server and make them get notifications
    
    try:
        connectDevices = await e.setupConnectivity(devices=[HUB, STR, FWD, RWD, ])
    except TimeoutError:
        print(f"{C.BOLD}{C.FAIL}SETUP TIMED OUT{C.ENDC}\r\n"
              f"CONNECTED DEVICES: ")
        return
    print(f"\t\t{C.BOLD}{C.UNDERLINE}{C.OKBLUE}****************DEVICE SETUP DONE****************{C.ENDC}\r\n")
    
    #taskList: defaultdict = defaultdict(list)
    
    
    #taskList['t0'] = [
            # {'cmd': RWD.GOTO_ABS_POS(position=-400, abs_max_power=100, speed=50)},
            # {'cmd': RWD.GOTO_ABS_POS(position=200, abs_max_power=100, speed=50)},
            # {'cmd': RWD.START_MOVE_DISTANCE(distance=1500.0, speed=100, abs_max_power=100)},
            # {'cmd': FWD_RWD.GOTO_ABS_POS_SYNCED(abs_pos_a=1000, abs_pos_b=1000, speed=60, abs_max_power=90)},
            # {'cmd': FWD_RWD.GOTO_ABS_POS_SYNCED(abs_pos_a=-1000, abs_pos_b=-1000, speed=100, abs_max_power=100)},
            # {'cmd': FWD_RWD.START_SPEED_TIME(time=5000, speed=80, power=100, start_cond=MOVEMENT.ONSTART_BUFFER_IF_NEEDED)},
            # {'cmd': RWD.START_SPEED_TIME(time=5000, speed=-100, power=100, start_cond=MOVEMENT.ONSTART_BUFFER_IF_NEEDED, delay_after=0.1)},
            # {'cmd': FWD.START_SPEED_TIME(time=5000, speed=100, power=100, start_cond=MOVEMENT.ONSTART_BUFFER_IF_NEEDED, delay_after=0.1)},
            # {'cmd': FWD_RWD.START_SPEED_TIME(time=5000, speed=-100, power=100, start_cond=MOVEMENT.ONSTART_BUFFER_IF_NEEDED)},
            
 #           ]
#
    # cal_STR: defaultdict = defaultdict(list)
    # cal_STR["t0"] = [{'cmd': STR.START_MOVE_DEGREES(degrees=180, speed=40, on_stalled=STR.STOP())},
       #              ]
  #  testStop: defaultdict = defaultdict(list)
    #testStop["t0"] = [#{'cmd': RWD.START_SPEED_TIME(speed=-100, power=100, time=10000)},
                      #{'cmd': RWD.START_SPEED_TIME(speed=100, power=100, time=2500)},
                      #{'cmd': RWD.STOP(delay_before=2.5936)},
                      # {'cmd': FWD.START_SPEED_UNREGULATED(speed=100, abs_max_power=100)},
                      #{'cmd': RWD.SET_POSITION(delay_before=2.0)},
                      #{'cmd': RWD.START_SPEED_TIME(speed=100, power=100, time=10000, on_stalled=RWD.STOP(), time_to_stalled=0.001)},
                      #{'cmd': RWD.START_SPEED_TIME(speed=-100, power=100, time=10000)},
                      #{'cmd': RWD.START_SPEED_UNREGULATED(speed=100, abs_max_power=100)},
     #                 ]
    # result_t0 = await asyncio.wait_for(e.run_each(tasklist=cal_STR), timeout=None)
    #result_t1 = await asyncio.wait_for(e.run_each(tasklist=testStop), timeout=None)
    print('Starting in 5')
    await asyncio.sleep(5)
    await STR.SET_ACC_PROFILE(ms_to_full_speed=0, profile_nr=0, cmd_id='ACC PROFILE 0')
    await STR.SET_DEC_PROFILE(ms_to_zero_speed=5, profile_nr=0, cmd_id='DEC Profile 0')
    speed = 40
    # STR.STOP(cmd_id='STOP1')
    await STR.START_MOVE_DEGREES(on_stalled=STR.STOP(cmd_id='1st STOP'), degrees=180, speed=-speed, abs_max_power=50, cmd_id='1st EXTREME')
    await STR.SET_POSITION(0, cmd_id='1st SET_POS')
    speed = 40
    print(f"JUST CHECKING: 1st POS_RESET IN DEG: \t {STR.port_value.m_port_value_DEG}")
    await STR.START_MOVE_DEGREES(on_stalled=STR.STOP(cmd_id='2nd STOP'), degrees=180, speed=speed, abs_max_power=50, cmd_id='2nd EXTREME')
    max_deg = abs(STR.port_value.m_port_value_DEG)
    debug_info(f"{C.BOLD}{C.FAIL}MAX: {max_deg}", debug=True)
    mid = int(round((max_deg / 2)))
    print(f"MID POS: {mid}")
    await STR.SET_POSITION(0, cmd_id='2nd SET_POS')
    print(f"JUST CHECKING 2nd POS_RESET: POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    ## STR.STOP(cmd_id='STOP3')
    await STR.START_MOVE_DEGREES(on_stalled=STR.STOP(cmd_id='3rd STOP'), degrees=mid, speed=-speed, abs_max_power=100, cmd_id='GO_ZERO')
    await STR.SET_POSITION(0)
    print(f"JUST CHECKING 3rd POS_RESET: POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    print(f"FINISHED FINISHED FINISHED")
    # await STR.SET_POSITION(pos=0)
    # await STR.START_MOVE_DEGREES(degrees=180, speed=-40, abs_max_power=60, on_stalled=STR.STOP())
    # mid_pos = int(round(STR.port_value.m_port_value_DEG/2))
    # STR.max_steering_angle = abs(mid_pos)
    # await STR.START_MOVE_DEGREES(degrees=mid_pos, speed=40, abs_max_power=60, on_stalled=STR.STOP())
    # await STR.SET_POSITION(pos=0)
    
    while True:
        
        await asyncio.sleep(1.0)
    
if __name__ == '__main__':
    """This is the loading programme.
    
    It can be but is not intended to be modified.
    
    Nothing really special here.
    
    """
    loopy = asyncio.get_event_loop()
    
    t0 = datetime.timestamp(datetime.now())
    asyncio.run(main(), debug=True)
    loopy.run_forever()
    print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
