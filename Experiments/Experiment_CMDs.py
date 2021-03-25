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
from LegoBTLE.LegoWP.types import HUB_ACTION
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
    FWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x01', name='FWD', gearRatio=2.67)
    STR: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x02', name='STR', gearRatio=2.67)
    RWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x00', name='RWD', gearRatio=1.00)
    
    experimentActions = [
            {'cmd': HUB.connect_ext_srv, 'task': {'p_id': 'HUBCON', 'waitUntil': False}},
            {'cmd': STR.connect_ext_srv, 'task': {'p_id': 'STRCON', 'waitUntil': False}},
            {'cmd': FWD.connect_ext_srv, 'task': {'p_id': 'FWDCON', 'delay_before': 0.0, 'delay_after': 0.0, 'waitUntil': True}},
            {'cmd': RWD.connect_ext_srv, 'task': {'p_id': 'RWDCON', 'waitUntil': True}},
            {'cmd': HUB.GENERAL_NOTIFICATION_REQUEST, 'task': {'p_id': 'HUBNOTIF', 'waitUntil': True}},
            {'cmd': HUB.HUB_ACTION, 'kwargs': {'action': HUB_ACTION.DNS_HUB_INDICATE_BUSY_ON}, 'task': {'p_id': 'HUBACTIONBUSYON', 'delaybefore': 2.0,
                                                                                                        'waitUntil': True}},
            {'cmd': FWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'FWDNOTIF', 'waitUntil': False}},
            {'cmd': STR.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'STRNOTIF', 'waitUntil': False}},
            {'cmd': RWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'RWDNOTIF', 'waitUntil': True}},
            {'cmd': RWD.START_POWER_UNREGULATED, 'kwargs': {'power': -90, 'abs_max_power': 100}, 'task': {'p_id': 'RWD_STARTSPEED',
                                                                                                          'delay_before': 0.0, 'delay_after': 3.0, 'waitUntil': False}},
            {'cmd': RWD.START_POWER_UNREGULATED, 'kwargs': {'abs_max_power': 90, 'power': 60}, 'task': {'p_id': 'RWDSTARTSPEED_REV', 'delay_before': 3.0, 'waitUntil': False}},
            {'cmd': RWD.START_POWER_UNREGULATED, 'kwargs': {'abs_max_power': 0, 'power': 0}, 'task': {'p_id': 'RWD_STOP', 'delay_before': 3.0, 'waitUntil': False}}
            ]
    
    experimentTasks1 = [
            {'cmd': HUB.connect_ext_srv, 'task': {'p_id': 'HUBCON', 'waitUntil': False}},
            {'cmd': STR.connect_ext_srv, 'task': {'p_id': 'STRCON', 'waitUntil': False}},
            {'cmd': FWD.connect_ext_srv, 'task': {'p_id': 'FWDCON', 'delay_before': 0.0, 'delay_after': 0.0, 'waitUntil': True}},
            {'cmd': RWD.connect_ext_srv, 'task': {'p_id': 'RWDCON', 'waitUntil': True}},
            {'cmd': HUB.GENERAL_NOTIFICATION_REQUEST, 'task': {'p_id': 'HUBNOTIF', 'waitUntil': True}},
            {'cmd': FWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'FWDNOTIF', 'waitUntil': False}},
            {'cmd': STR.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'STRNOTIF'}},
            {'cmd': RWD.REQ_PORT_NOTIFICATION, 'task': {'p_id': 'RWDNOTIF', 'waitUntil': RWD.port_free.is_set}},
            ]
    
    # t0 = await asyncio.wait_for(e.createAndRun(experimentActions, loop=loopy), timeout=None)
    
    # print(f"the results of this Run are:")
    # for tr in t0:
    #     print(f"{tr}")
    
    t1 = await asyncio.wait_for(e.createAndRun(connectAndSetNotify([HUB,
                                                                    FWD,
                                                                    STR,
                                                                    RWD, ]), loop=loopy), timeout=None)
    
    for tr in t1:
        pass
    print(f"RESULT: {t1}")
    loopy.stop()
    return


if __name__ == '__main__':
    """This is the loading programme.
    
    It can be but is not intended to be modified.
    
    Nothing really special here.
    
    """
    loopy = asyncio.get_event_loop()
    try:
        t0 = datetime.timestamp(datetime.now())
        asyncio.run(main())
        print(f"Overall RUNTIME: {datetime.timestamp(datetime.now()) - t0}")
        if loopy.is_running():
            loopy.run_until_complete(loopy.shutdown_asyncgens())
        else:
            loopy.close()
    except KeyboardInterrupt:
        print(f"SHUTTING DOWN...")
        loopy.run_until_complete(loopy.shutdown_asyncgens())
        loopy.stop()
    
        loopy.close()

