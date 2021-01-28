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
from threading import Thread, Event, current_thread
from queue import Queue
from time import sleep

from LegoBTLE.Constants.Port import Port
from LegoBTLE.Controller.THub import Hub
from LegoBTLE.Device.TMotor import Motor, SingleMotor


def startSystem(hub: Hub, motors: [Motor]) -> ([Thread], Event):
    E_SYSTEM_STARTED: Event = Event()
    ret: [Thread] = []
    hub.requestNotifications()

    ret.append(Thread(name="BTLE NOTIFICATION LISTENER", target=hub.listenNotif,
                      daemon=True))

    ret.append(Thread(name="HUB COMMAND SENDER", target=hub.rslt_snd,
                      daemon=True))

    ret.append(Thread(name="HUB COMMAND RECEIVER", target=hub.res_rcv,
                      daemon=True))

    for motor in motors:
        motor.requestNotifications()
        hub.register(motor)
        ret.append(Thread(name="{} SENDER".format(motor.name), target=motor.CmdSND, daemon=True))
        ret.append(Thread(name="{} RECEIVER".format(motor.name), target=motor.RsltRCV, daemon=True))

    for r in ret:
        r.start()
        r.start()
    E_SYSTEM_STARTED.set()
    return ret, E_SYSTEM_STARTED


def stopSystem(hub: Hub, motors: [Motor]) -> Event:
    E_SYSTEM_STOPPED: Event = Event()
    terminate.set()
    print("[{}]-[MSG]: COMMENCE SHUTDOWN...".format(current_thread().name))
    T_HUB_RCV.join(2)
    T_HUB_SEND.join(2)
    T_NOTIFICATIONS_LISTENER.join(10)
    T_VORDERRADANTRIEN_SND.join(2)
    T_VORDERRADANTRIEN_RCV.join(2)
    hub.shutDown()
    return E_SYSTEM_STOPPED


if __name__ == '__main__':

    terminate: Event = Event()
    cmdQ: Queue = Queue(maxsize=50)

    #  BEGIN HUB Spec
    hub: Hub = Hub(address='90:84:2B:5E:CF:1F', name="Threaded Hub", cmdQ=cmdQ, terminate=terminate, debug=True)

    #  END HUB Spec
    #  BEGIN Motor Spec
    motors: [Motor] = [SingleMotor(name="Vorderradantrieb", port=Port.A, gearRatio=2.67, cmdQ=cmdQ, terminate=terminate,
                                   debug=True)]
    startSystem(hub=hub, motors=motors)[1].wait()
    #  END Motor Spec
    #  commands

    sleep(60)

    print("[{}]-[MSG]: SHUTDOWN COMPLETE...".format(current_thread().name))
