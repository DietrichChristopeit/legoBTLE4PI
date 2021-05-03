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
from typing import List

from legoBTLE.device.Hub import Hub
from legoBTLE.device.SingleMotor import SingleMotor
from legoBTLE.legoWP.types import MOVEMENT
from legoBTLE.user.Experiment import Experiment


async def main(loop: AbstractEventLoop):
    """Main function to define an run_each an Experiment in.

    This function should be the sole entry point for using the whole project.
    
    :param AbstractEventLoop loop: The EventLoop that main() is running in.
    :type loop: AbstractEventLoop
    :returns: Nothing
    :rtype: None
    
    """
    # time.sleep(5.0) # for video, to have time to fumble with the phone keys :-)

    e: Experiment = Experiment(name='Experiment0', measure_time=True, debug=True)
    
    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888), debug=True)
    FWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x01', name='FWD', gearRatio=2.67)
    STR: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x02', name='STR', gearRatio=2.67)
    RWD: SingleMotor = SingleMotor(server=('127.0.0.1', 8888), port=b'\x00', name='RWD', gearRatio=1.00)

    experimentActions: List[e.Action] = [e.Action(cmd=HUB.EXT_SRV_CONNECT_REQ, only_after=False),
                                         e.Action(cmd=FWD.EXT_SRV_CONNECT_REQ, only_after=False),
                                         e.Action(cmd=STR.EXT_SRV_CONNECT_REQ, only_after=False),
                                         e.Action(cmd=RWD.EXT_SRV_CONNECT_REQ),

                                         e.Action(cmd=HUB.GENERAL_NOTIFICATION_REQUEST),
                                         #e.Action(cmd=HUB.HUB_ACTION,
                                          #        kwargs={'action': HUB_ACTION.DNS_HUB_INDICATE_BUSY_ON}),
                                         e.Action(cmd=FWD.REQ_PORT_NOTIFICATION),
                                         e.Action(cmd=STR.REQ_PORT_NOTIFICATION),
                                         e.Action(cmd=RWD.REQ_PORT_NOTIFICATION),
                                         
                                         e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 70,
                                                                                    'direction': MOVEMENT.FORWARD,
                                                                                    'on_completion': MOVEMENT.BREAK,
                                                                                    'power': 100, 'time': 5000}),
                                         
                                         e.Action(cmd=FWD.START_SPEED_TIME, kwargs={'speed': 100,
                                                                                    'direction': MOVEMENT.REVERSE,
                                                                                    'on_completion': MOVEMENT.COAST,
                                                                                    'power': 100, 'time': 5000}),
                                         
                                         e.Action(cmd=FWD.START_SPEED_TIME, kwargs={'speed': 10,
                                                                                    'direction': MOVEMENT.FORWARD,
                                                                                    'on_completion': MOVEMENT.BREAK,
                                                                                    'power': 30, 'time': 5000}),
                                         
                                         e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 65,
                                                                                    'direction': MOVEMENT.REVERSE,
                                                                                    'on_completion': MOVEMENT.COAST,
                                                                                    'power': 60, 'time': 5000}),
                                         
                                         e.Action(cmd=STR.START_SPEED_TIME, kwargs={'speed': 10,
                                                                                    'direction': MOVEMENT.RIGHT,
                                                                                    'on_completion': MOVEMENT.BREAK,
                                                                                    'power': 100, 'time': 800}),
                                         ]
    
    e.append(experimentActions)
    taskList, runtime = e.runExperiment()

    print(f"Total execution time: {runtime}")

    # keep alive
    while True:
        await asyncio.sleep(.5)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(loop=loop))
    loop.run_forever()
