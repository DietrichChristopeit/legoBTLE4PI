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
import time
from asyncio import AbstractEventLoop

# first, we need a event_loop running in a parallel Thread
from collections.abc import Coroutine
from typing import Any, Callable, Optional, Union

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.exceptions.value_execptions import NoneError
from LegoBTLE.networking.client import CMD_Client


class Experiment:
    
    def __init__(self, event_loop: AbstractEventLoop = None):
        if event_loop is None:
            raise NoneError(f"Argument loop must not be {event_loop}...")
        self._event_loop = event_loop
        self._cmd_Client: CMD_Client = CMD_Client()
        return
    
    @property
    def cmd_client(self) -> CMD_Client:
        return self._cmd_Client
    
    def exec(self, cmd=None, args=None, kwargs=None):
        
        (done, pending) = loop.run_until_complete(
                asyncio.ensure_future(
                        asyncio.wait(
                                (
                                        asyncio.ensure_future(
                                                cmd(*args or [], **kwargs or {}),
                                                loop=self._event_loop),),
                                timeout=0.1
                                ),
                        loop=self._event_loop
                        )
                )
        return done, pending


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    experiment: Experiment = Experiment(event_loop=loop)
    devices = [
            Hub(name="THE LEGO HUB 2.0"),
            SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67),
            SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67),
            SingleMotor(name="STR", port=b'\x02'),
            ]
    # FWD_RWD = SynchronizedMotor(name="FWD_RWD", motor_a=FWD, motor_b=RWD)
    
    # adding Hub
    for d in devices:
        experiment.exec(cmd=experiment.cmd_client.DEV_CONNECT_SRV, kwargs={'device': d, 'wait': True})
        experiment.exec(cmd=experiment.cmd_client.DEV_LISTEN_SRV, kwargs={'device': d, 'wait': True})
        # event_loop.run_until_complete(asyncio.ensure_future(pack(cmd=cmd_client.DEV_CONNECT_SRV, kwargs={'device': d, 'wait': True}), event_loop=event_loop))
    time.sleep(3)
    for d in devices[1:]:
        done, pending = experiment.exec(cmd=d.REQ_PORT_NOTIFICATION, kwargs={'wait': False})
        for de in done:
            print(f"RESULT: {de.result()}")
        for pe in pending:
            print(f"RESULT: {pe.result()}")
    
    print(f"disconnect")
    for d in devices:
        experiment.exec(cmd=experiment.cmd_client.DEV_DISCONNECT_SRV, kwargs={'device': d, 'wait': True})
    print(f"Start agsin...")
    time.sleep(3)
    for d in devices:
        experiment.exec(cmd=experiment.cmd_client.DEV_CONNECT_SRV, kwargs={'device': d, 'wait': True})
        experiment.exec(cmd=experiment.cmd_client.DEV_LISTEN_SRV, kwargs={'device': d, 'wait': True})
    
    print("running forever")
    loop.run_forever()
