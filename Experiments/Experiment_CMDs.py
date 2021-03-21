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
from asyncio import AbstractEventLoop

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import HUB_ACTION
from LegoBTLE.User.executor import Experiment


async def main():
    """Main function to define an run an Experiment in.

    This function should be the sole entry point for using the whole project.

    :param AbstractEventLoop loop: The EventLoop that main() is running in.
    :type loop: AbstractEventLoop
    :returns: Nothing
    :rtype: None

    """
    # time.sleep(5.0) # for video, to have time to fumble with the phone keys :-)
    loopy = asyncio.get_running_loop()
    e: Experiment = Experiment(name='Experiment0', measure_time=True, debug=True)

    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888), debug=True)
    FWD: SingleMotor = SingleMotor(name='FWD', port=b'\x01', server=('127.0.0.1', 8888), gearRatio=2.67)
    STR: SingleMotor = SingleMotor(name='STR', port=b'\x02', server=('127.0.0.1', 8888), gearRatio=2.67)
    RWD: SingleMotor = SingleMotor(name='RWD', port=b'\x00', server=('127.0.0.1', 8888), gearRatio=1.00)

    experimentActions = [
            {'cmd': HUB.connect_ext_srv, 'task': {'id': 'HUBCON', 'wait_for': False}},
            {'cmd': FWD.connect_ext_srv, 'task': {'id': 'FWDCON', 'wait_for': False}},
            {'cmd': STR.connect_ext_srv, 'task': {'id': 'STRCON', 'wait_for': False}},
            {'cmd': RWD.connect_ext_srv, 'task': {'id': 'STRCON', 'wait_for': True}},
            {'cmd': HUB.GENERAL_NOTIFICATION_REQUEST, 'task': {'id': 'HUBNOTIF', 'wait_for': True}},
            {'cmd': HUB.HUB_ACTION, 'kwargs': {'action': HUB_ACTION.DNS_HUB_INDICATE_BUSY_ON}, 'task': {'id': 'HUBACTIONBUSYON', 'delaybefore': 2.0}},
            {'cmd': FWD.REQ_PORT_NOTIFICATION, 'task': {'id': 'FWDNOTIF', 'wait_for': True}},
            {'cmd': STR.REQ_PORT_NOTIFICATION, 'task': {'id': 'STRNOTIF', 'wait_for': True}},
            {'cmd': RWD.REQ_PORT_NOTIFICATION, 'task': {'id': 'RWDNOTIF', 'wait_for': True}},
            {'cmd': RWD.START_POWER_UNREGULATED, 'kwargs': {'power': -90, 'abs_max_power': 100}, 'task': {'id': 'RWD_STARTSPEED', 'delayafter': 3.0, 'waitfor': False}},
            {'cmd': RWD.START_POWER_UNREGULATED, 'kwargs': {'abs_max_power': 90, 'power': 60}, 'task': {'id': 'RWDSTARTSPEED_REV', 'delayafter': 3.0, 'waitfor': False}},
            ]

    t = asyncio.create_task(e.createAndRun(experimentActions, loop=loopy))

    print(f"Total execution time:")

if __name__ == '__main__':
    loopy = asyncio.get_event_loop()
    try:
        asyncio.run(main())
        loopy.run_forever()
    except KeyboardInterrupt:
        print(f"SHUTTING DOWN...")
        loopy.run_until_complete(loopy.shutdown_asyncgens())
        loopy.stop()
    
        loopy.close()

