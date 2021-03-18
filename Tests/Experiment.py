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
from time import monotonic
from typing import List

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.LegoWP.types import MOVEMENT
from LegoBTLE.User.executor import Experiment


async def main(loop: AbstractEventLoop):
    """
    Main function to define an run an Experiment in.
    This function should be the sole entry point for using the whole project.
    
    :param AbstractEventLoop loop: The EventLoop that main is running in.
    :type loop: AbstractEventLoop
    :returns: Nothing
    :rtype: None
    
    """
    e: Experiment = Experiment(name='Experiment0', measure_time=True)
    
    HUB: Hub = Hub(name='LEGO HUB 2.0', server=('127.0.0.1', 8888))
    FWD: SingleMotor = SingleMotor(name='FWD', port=b'\x01', server=('127.0.0.1', 8888), gearRatio=2.67)
    STR: SingleMotor = SingleMotor(name='STR', port=b'\x02', server=('127.0.0.1', 8888), gearRatio=2.67)
    RWD: SingleMotor = SingleMotor(name='RWD', port=b'\x00', server=('127.0.0.1', 8888), gearRatio=1.00)

    al: [[e.Action]] = [e.Action(cmd=HUB.connect_ext_srv),
                        e.Action(cmd=FWD.connect_ext_srv),
                        e.Action(cmd=RWD.connect_ext_srv, only_after=True),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 780}),
                        e.Action(cmd=FWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 780}),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 930}),
                        e.Action(cmd=STR.connect_ext_srv, only_after=True),
                        e.Action(cmd=STR.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 70, 'abs_pos': 10}),
                        e.Action(cmd=RWD.GOTO_ABS_POS,
                                 kwargs={'on_completion': MOVEMENT.COAST, 'abs_max_power': 100, 'abs_pos': 800},
                                 only_after=True),
                        ]

    al1: List[e.Action] = [e.Action(cmd=FWD.connect_ext_srv, only_after="Hallo"),
                           e.Action(cmd=FWD.listen_srv),
                           e.Action(cmd=HUB.connect_ext_srv, only_after=True),
                           e.Action(cmd=HUB.GENERAL_NOTIFICATION_REQUEST),
                           e.Action(cmd=HUB.listen_srv),
                           e.Action(cmd=FWD.REQ_PORT_NOTIFICATION, only_after=True),
                           e.Action(cmd=FWD.GOTO_ABS_POS,
                                    kwargs={'abs_pos': 70, 'abs_max_power': 90, 'on_completion': MOVEMENT.COAST,
                                            'speed': 80
                                            }),
                           ]

    al2: List[e.Action] = [e.Action(cmd=HUB.connect_ext_srv),
                           e.Action(cmd=FWD.connect_ext_srv),
                           e.Action(cmd=RWD.connect_ext_srv, only_after=True),
                           e.Action(cmd=HUB.GENERAL_NOTIFICATION_REQUEST),
                           e.Action(cmd=FWD.REQ_PORT_NOTIFICATION),
                           e.Action(cmd=RWD.REQ_PORT_NOTIFICATION, only_after=True),
                           e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 100, 'direction': MOVEMENT.FORWARD,
                                                                      'on_completion': MOVEMENT.BREAK, 'power': 100,
                                                                      'time': 5000}),
                           e.Action(cmd=FWD.START_SPEED_TIME, kwargs={'speed': 100, 'direction': MOVEMENT.FORWARD,
                                                                      'on_completion': MOVEMENT.BREAK, 'power': 100,
                                                                      'time': 5000}),
                           e.Action(cmd=RWD.START_SPEED_TIME, kwargs={'speed': 100, 'direction': MOVEMENT.REVERSE,
                                                                      'on_completion': MOVEMENT.BREAK, 'power': 100,
                                                                      'time': 5000}),
                           ]
    e.append(al2)
    taskList = e.runExperiment(saveResults=True)
    t0 = monotonic()
    
    for k in list(taskList.keys()):
        print(f"AWAITING BATCH AFTER BATCH: {k}")
        done = asyncio.gather(taskList[k])
        for d in done:
            print(f"{d}")
            
    # print(f"waiting 30.0")
    # await sleep(30.0)
    # print(f"LAST COMMAND SUCCESSFUL: {FWD.last_cmd_snt.COMMAND.hex() if FWD.last_cmd_snt is not None else None}")
    # print(f"LAST COMMAND SUCCESSFUL: {HUB.last_cmd_snt.COMMAND.hex() if HUB.last_cmd_snt is not None else None}")
    # print(f"LAST COMMAND FAILED: {FWD.last_cmd_failed.COMMAND.hex() if FWD.last_cmd_failed is not None else None}")
    # print(f"SERVER LOG (seen from Device {FWD.name}): {FWD.hub_attached_io_notification}")
    # print(f"SERVER LOG (seen from Device {RWD.name}): {RWD.ext_srv_notification_log}")
    # print(f"SERVER LOG (seen from Device {STR.name}): {STR.ext_srv_notification_log}")
    # print(f"SERVER LOG (seen from Device {HUB.name}): {HUB.ext_srv_notification_log}")
    # e.getState()
    # print(f"Saved results: {e.savedResults}")
    # for r in e.getDoneTasks():
    #     print(f"Result of Task: {r} = {r.result()}")
    # print(f"Experiment {e.name} exec took: {e.runTime} sec.")
    # print(f"Overall runTime took: {monotonic() - t0} sec.")
    # await sleep(.5)
#
    # prev = '0'
#
    # while True:
#
    #     if RWD.port_value is not None:
    #         if RWD.port_value.m_port_value.hex() != prev:
    #             prev = RWD.port_value.m_port_value.hex()
    #             print(f"VALUE: {prev}")
    #     await sleep(.01)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.run(main(loop=loop))
    loop.run_forever()
