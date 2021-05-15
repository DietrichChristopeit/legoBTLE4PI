# coding=utf-8
"""
MainProgs.Experiment_CMDS
=========================

This Packet is a collection of examples and how to use them.

The Experiment Example
----------------------

    Here some example action sequences are defined that the Lego(c) Model should perform.

    It could be used as a template for other experiments.

Basic Structure:
................

    1.  Install all devices you want to operate.
    2.  Start the Server :class:`legoBTLE.networking.server`
    3.  Connect all devices with the :class:`legoBTLE.networking.server`
    4.  Issue commands.

"""
import asyncio
from datetime import datetime

from legoBTLE.device.Hub import Hub
from legoBTLE.device.SingleMotor import SingleMotor
from legoBTLE.device.SynchronizedMotor import SynchronizedMotor
from legoBTLE.legoWP.types import C
from legoBTLE.legoWP.types import CCW
from legoBTLE.legoWP.types import CW
from legoBTLE.legoWP.types import MESSAGE_STATUS
from legoBTLE.legoWP.types import MOVEMENT
from legoBTLE.legoWP.types import PORT
from legoBTLE.networking.prettyprint.debug import debug_info
from legoBTLE.networking.prettyprint.debug import debug_info_footer
from legoBTLE.networking.prettyprint.debug import prg_out_msg
from legoBTLE.user.Experiment import Experiment


async def main():
    """Main function to define and run_each an Experiment in.

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
                                       gear_ratio=2.67,
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

# time.sleep(5.0) # for video, to have time to fumble with the phone keys :-)
    
    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0',
                               measure_time=False,
                               loop=loopy,
                               debug=True,
                               )
    # device definitions
    HUB: Hub = Hub(name='LEGO HUB 2.0',
                   server=('127.0.0.1', 8888),
                   debug=True,)
    
    RWD: SingleMotor = SingleMotor(name='RWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.B,
                                   gear_ratio=2.67,
                                   clockwise=MOVEMENT.COUNTERCLOCKWISE,
                                   wheel_diameter=100.0,
                                   time_to_stalled=0.2,
                                   stall_bias=0.2,
                                   debug=True,
                                   )
    
    STR: SingleMotor = SingleMotor(name=f"{C.HEADER}STEERING MOTOR{C.ENDC}",
                                   server=('127.0.0.1', 8888),
                                   port=PORT.C,
                                   gear_ratio=0.625,
                                   time_to_stalled=0.2,
                                   stall_bias=0.2,
                                   clockwise=MOVEMENT.CLOCKWISE,
                                   debug=True, )
    
    FWD: SingleMotor = SingleMotor(name='FWD',
                                   server=('127.0.0.1', 8888),
                                   port=PORT.A,
                                   gear_ratio=2.67,
                                   wheel_diameter=100.0,
                                   clockwise=MOVEMENT.COUNTERCLOCKWISE,
                                   debug=True,
                                   )
    
    FWD_RWD: SynchronizedMotor = SynchronizedMotor(name='FWD_RWD_SYNC',
                                                   motor_a=FWD,
                                                   motor_b=RWD,
                                                   server=('127.0.0.1', 8888),
                                                   stall_bias=0.2,
                                                   time_to_stalled=0.2,
                                                   debug=True,
                                                   )
     
    # Connect the devices with the Server and make them get notifications
    
    try:
        connectdevices = await e.setupConnectivity(devices=[HUB, STR, FWD, RWD, FWD_RWD])
    except TimeoutError:
        prg_out_msg(f"SETUP TIMED OUT", MESSAGE_STATUS.FAILED)
        return
    debug_info_footer(f"DEVICE SETUP DONE", debug=True)
    
    #await FWD_RWD.START_MOVE_DEGREES(degrees=1440, abs_max_power=100, speed=CCW(100), on_stalled=FWD_RWD.STOP(cmd_id='STOP FWD_RWD'), cmd_debug=True, cmd_id='FWD_RWD.TURN DEGREES')
    
    # await RWD.START_MOVE_DEGREES(degrees=1440, speed=CW(100), abs_max_power=100, on_stalled=RWD.STOP(cmd_id="RWD:STOP"), cmd_id="RWD MOTOR")
    # await RWD.START_MOVE_DEGREES(degrees=1440, speed=CCW(100), abs_max_power=100, on_stalled=RWD.STOP(cmd_id="RWD:STOP AAA"),
    #                             cmd_id="RWD MOTOR")

    # taskList: defaultdict = defaultdict(list)
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
    
# ############################### carlibrate Motor STR  ################################
    prg_out_msg('Starting motors in 5')
    await asyncio.sleep(5)
    # await STR.SET_ACC_PROFILE(ms_to_full_speed=0, profile_nr=0, cmd_id='ACC PROFILE 0')
    # await STR.SET_DEC_PROFILE(ms_to_zero_speed=0, profile_nr=0, cmd_id='DEC PROFILE 0')
    speed = 40
    await STR.START_MOVE_DEGREES(cmd_id='1st EXTREME', on_stalled=STR.STOP(cmd_id='1st STOP'), degrees=180,
                                 speed=CCW(speed), abs_max_power=20, on_completion=MOVEMENT.COAST)
    await asyncio.sleep(1.0)
    await STR.SET_POSITION(0, cmd_id='1st SET_POS')
    speed = 40
    prg_out_msg(f"JUST CHECKING: 1st POS_RESET IN DEG: \t {STR.port_value.m_port_value_DEG}")
    await STR.START_MOVE_DEGREES(cmd_id='2nd EXTREME', on_stalled=STR.STOP(cmd_id='2nd STOP'), degrees=288,
                                 speed=CW(speed), abs_max_power=20, on_completion=MOVEMENT.COAST)
    await asyncio.sleep(1.0)
    max_deg = abs(STR.port_value.m_port_value_DEG)
    debug_info(f"{C.BOLD}{C.FAIL}MAX: {max_deg}", debug=True)
    mid = int(round((max_deg / 2)))
    STR.max_steering_angle = abs(mid)
    prg_out_msg(f"MID POS: {mid}")
    await STR.SET_POSITION(0, cmd_id='2nd SET_POS')
    prg_out_msg(f"JUST CHECKING 2nd POS_RESET: POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    
    await STR.START_MOVE_DEGREES(on_stalled=STR.STOP(cmd_id='3rd STOP'), degrees=mid, speed=CCW(speed), abs_max_power=100,
                                 cmd_id='GO_ZERO', on_completion=MOVEMENT.COAST)
    await STR.SET_POSITION(0)
    prg_out_msg(f"JUST CHECKING 3rd POS_RESET: POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    prg_out_msg(f"FINISHED FINISHED FINISHED")
    await STR.START_MOVE_DEGREES(on_stalled=STR.STOP(cmd_id='30° RIGHT STOP'), degrees=30, speed=CW(40), abs_max_power=40,
                                 cmd_id='30° RIGHT')
    prg_out_msg(f"JUST CHECKING '30° RIGHT': POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    await STR.GOTO_ABS_POS(on_stalled=STR.STOP(cmd_id='4th STOP'), position=0, speed=CCW(40), abs_max_power=40,
                           cmd_id='0° mid 1.')
    await STR.GOTO_ABS_POS(on_stalled=STR.STOP(cmd_id='5th STOP'), position=0, speed=CW(40), abs_max_power=40,
                           cmd_id='0° mid 2.')
    prg_out_msg(f"JUST CHECKING '0°' 2.: POS IN DEG: \t {STR.port_value.m_port_value_DEG}")
    
    await RWD.START_SPEED_TIME(5000, CW(80), on_stalled=RWD.STOP(cmd_id='RWD STOP', cmd_debug=True), cmd_id='RWD SPEED TIME')
    
    while True:
        prg_out_msg(f"JUST CHECKING '0° LEFT': POS IN DEG: \t {STR.last_value.m_port_value_DEG}")
        await asyncio.sleep(1.0)
        
    
    #  ############################## Drive For 10 meter ################################
    #  prg_out_msg(f"DRIVE for 1m")
    #  await FWD.SET_ACC_PROFILE(ms_to_full_speed=4000, profile_nr=1, cmd_debug=True)
    #  await FWD.SET_DEC_PROFILE(ms_to_zero_speed=5000, profile_nr=1, cmd_debug=True)
    #  await FWD.START_MOVE_DISTANCE(10000, CCW(100), abs_max_power=100, on_completion=MOVEMENT.HOLD, use_profile=1, use_acc_profile=MOVEMENT.USE_ACC_PROFILE, use_dec_profile=MOVEMENT.USE_DEC_PROFILE)
    #  ############################# END: DRIVE FOR 1 m ################################
    
if __name__ == '__main__':
    """This is the loading programme.
    
    It can be but is not intended to be modified.
    
    Nothing really special here.
    
    """
    loopy = asyncio.get_event_loop()
    
    t0 = datetime.timestamp(datetime.now())
    asyncio.run(main(), debug=False)
    loopy.run_forever()
    print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
