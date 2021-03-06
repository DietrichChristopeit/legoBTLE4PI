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

from LegoBTLE.Device.AHub import Hub
from LegoBTLE.Device.SingleMotor import SingleMotor
from LegoBTLE.Device.SynchronizedMotor import SynchronizedMotor
from LegoBTLE.LegoWP.types import ECMD
from LegoBTLE.User.experiment import Experiment

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    # reader, writer = loop.run_until_complete(asyncio.open_connection(host='127.0.0.1', port=8888))
    
    devices = [Hub(name="THE LEGO HUB 2.0"),
               SingleMotor(name="FWD", port=b'\x00', gearRatio=2.67),
               SingleMotor(name="RWD", port=b'\x01', gearRatio=2.67),
               SingleMotor(name="STR", port=b'\x02')
               ]
    
    experiment: Experiment = Experiment(devices=devices)
    
    # First CMD SEQUENCE: Connect the Devices to the Server using the CMD_Client
    
    #CONNECTION_SEQ = [ECMD(name=d.name, cmd=experiment.connect_listen_devices_srv, kwargs={'device': d}) for d in
     #                 devices]

    loop.run_until_complete(experiment.connect_listen_devices_srv(devices=devices, max_attempts=5))
    
    #print(CONNECTION_SEQ)
    #experiment.execute(cmd_sequence=CONNECTION_SEQ)
    
    loop.run_forever()
