#  MIT License
#
#  Copyright (c) 2021 Dietrich Christopeit
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
from colorama import Fore, Back, Style, init
from multiprocessing import Process, Queue, Event, Condition
from random import randint
from time import sleep

from LegoBTLE.Constants.Port import Port
from LegoBTLE.Controller.PHub import Hub
from LegoBTLE.Device.PMotor import SingleMotor

if __name__ == '__main__':
    init()

    Q_cmd_EXEC = Queue(maxsize=200)
    terminate: Event = Event()
    cond: Condition = Condition()
    print(Back.GREEN + Fore.BLACK + Style.BRIGHT + "{}: Starting up...".format(__name__))
    vorderradantrieb: SingleMotor = SingleMotor(name="Vorderradantrieb", port=Port.A, gearRatio=2.67, cmdQ=Q_cmd_EXEC, terminate=terminate, debug=True)
    # vorderradantrieb.startMotor()
    print(Style.NORMAL)
    with cond:
        hub: Hub = Hub(address='90:84:2B:5E:CF:1F', name="Jeep Hub", cmdQ=Q_cmd_EXEC, terminate=terminate, debug=True)
        hub.register(vorderradantrieb)
        e: Event = hub.startHub()
        cond.wait_for(lambda: e.is_set())
        print("SHutting down in 10")
        sleep(10)
        cond.notify_all()
    # vorderradantrieb.stopMotor()
    print("BETWEEN CONDS")
    with cond:
        e1: Event = hub.stopHub()
        cond.wait_for(lambda: e1.is_set())
        cond.notify_all()
    #hub.startHub()
    #sleep(20)
    #hub.stopHub()
    #vorderradantrieb.switchOffMotor()

    print(Back.GREEN + Fore.BLACK + Style.BRIGHT + "{}: SHUT DOWN COMPLETE...".format(__name__))
