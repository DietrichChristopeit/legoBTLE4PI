# coding=utf-8
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
from datetime import datetime

from Experiments.generators import connectAndSetNotify
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.User.executor import Experiment


async def main():
    """Main function to define an run an Experiment in.

    This function should be the sole entry point for using the whole project.
    
    :returns: None
    :rtype: None

    """
    # time.sleep(5.0) # for video, to have time to fumble with the phone keys :-)
    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0', measure_time=False, debug=True)

    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888), debug=True)
    RWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x01', name='RWD', gearRatio=2.67, debug=True)
    STR: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x02', name='STR', gearRatio=1.00, debug=True)
    FWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x00', name='FWD', gearRatio=2.67, debug=True)

    experimentTasks1 = [
        {'cmd': HUB.connect_ext_srv, 'task': {'p_id': 'HUBCON', 'waitUntil': False}},
        {'cmd': STR.connect_ext_srv, 'task': {'p_id': 'STRCON', 'waitUntil': False}},
        {'cmd': FWD.connect_ext_srv,
         'task': {'p_id': 'FWDCON', 'delay_before': 0.0, 'delay_after': 0.0, 'waitUntil': True}},
        {'cmd': RWD.connect_ext_srv, 'task': {'p_id': 'RWDCON', 'waitUntil': True}},
        {'cmd': HUB.GENERAL_NOTIFICATION_REQUEST, 'task': {'p_id': 'HUBNOTIF', 'waitUntil': True}},
        {'cmd': FWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'FWDNOTIF', 'waitUntil': False}},
        {'cmd': STR.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'STRNOTIF'}},
        {'cmd': RWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'RWDNOTIF', 'waitUntil': RWD.port_free.is_set}},
    ]

    t1 = await asyncio.wait_for(e.createAndRun(connectAndSetNotify([HUB,
                                                                    FWD,
                                                                    STR,
                                                                    RWD, ]), loop=loopy), timeout=None)

    experimentActions_USE_PROFILE = [

        {'cmd': RWD.SET_ACC_PROFILE, 'kwargs': {'ms_to_full_speed': 2000, 'profile_nr': 1, },
         'task': {'tp_id': 'HUB_ACC_PROFILE', }},
        {'cmd': RWD.SET_DEACC_PROFILE, 'kwargs': {'ms_to_zero_speed': 100, 'profile_nr': 1, },
         'task': {'tp_id': 'HUB_DEACC_PROFILE', }},

        {'cmd': RWD.START_SPEED_TIME,
         'kwargs': {'time': 10000,
                    'speed': 100,
                    'power': 100,
                    'on_completion': MOVEMENT.BREAK,
                    'use_profile': 1},
         'task': {'tp_id': 'RWD_GOTO', 'delay_before': 1.8, 'delay_after': 1.8}},
        {'cmd': RWD.START_SPEED_TIME,
         'kwargs': {'time': 10000,
                    'speed': -100,
                    'power': 100,
                    'on_completion': MOVEMENT.BREAK,
                    'use_profile': 1},
         'task': {'tp_id': 'RWD_GOTO1', 'delay_before': 1.8, 'delay_after': 1.8}},

    ]

    t0 = await asyncio.wait_for(e.createAndRun(experimentActions_USE_PROFILE, loop=loopy), timeout=None)

    while True:
        await asyncio.sleep(.012)

    print(f"RESULT: {t1}")

    return


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
