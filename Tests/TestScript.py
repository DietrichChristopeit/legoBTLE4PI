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
from queue import Queue
from threading import Event, Thread, Condition, current_thread
from time import sleep

from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Constants.Port import Port
from LegoBTLE.Controller.Hub import Hub
from LegoBTLE.Device.Motor import SingleMotor

if __name__ == '__main__':
    # BEGINN Initialisierung
    terminateEvent: Event = Event()
    terminateCondition: Condition = Condition()


    mainThread = current_thread()
    mainThread.setName("MAIN")

    hubExecQ: Queue = Queue(maxsize=3000)
    hubExecQEmptyEvent: Event = Event()
    hubStarted: Event = Event()
    hubStartedCondition: Condition = Condition()

    # ENDE Initialisierung

    hub: Hub = Hub(address='90:84:2B:5E:CF:1F', debug=True)
    hub.start()
    hub.HubStarted.wait()

    Vorderradantrieb: SingleMotor = SingleMotor("Vorderradantrieb", port=Port.A, gearRatio=2.67, hub=hub, debug=True)
    Hinterradantrieb: SingleMotor = SingleMotor("Hinterradantrieb", port=Port.B, gearRatio=2.67, hub=hub, debug=True)
    # Fahrtprogramm

    print("[{}]-[MSG]: starting Motor Threads...".format(mainThread.name))
    Vorderradantrieb.start()
    Hinterradantrieb.start()
    print("[{}]-[MSG]: Motor Threads STARTED...".format(mainThread.name))

    print("[{}]-[MSG]: waiting 15...".format(mainThread.name))
    sleep(15)
    # motorA.reset()
    # motorB.reset()
    # motorC.reset()
    print('Sending TURN FOR TIME to Motor {}'.format(Vorderradantrieb.name))
    gradAmAnfang = Vorderradantrieb.currentAngle
    Vorderradantrieb.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    Vorderradantrieb.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    gradAmEnde = Vorderradantrieb.currentAngle
    differenz = abs(gradAmEnde - gradAmAnfang)

    Vorderradantrieb.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data B to Motor A")
    # motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data A to Motor B")
    # motorB.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data C to Motor B")
    # motorB.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data B to Motor A")
    print('SENDING TURN FOR DEGREES to Motor {}'.format(Hinterradantrieb.name))
    Hinterradantrieb.turnForDegrees(3600, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK,
                                    withFeedback=True)
    # print("[{}]-[SIG]: WAITING FOR ALL COMMANDS TO END...".format(init()[3].name))
    # init()[2].wait()
    # print("[{}]-[SIG]: RESUME COMMAND EXECUTION RECEIVED...".format(init()[3].name))
    # print("Sending data C to Motor A")
    # motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data B to Motor B")
    # motorB.turnForDegrees(50, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    # print("Sending data B to Motor A")
    # motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.HOLD, withFeedback=True)
    # print("Sending data B to Motor A")
    # motorA.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.COAST, withFeedback=True)

    # print("[{}]-[MSG]: SHUTTING DOWN...".format(mainThread.name))
    sleep(2)

    hub.terminate()

    Hinterradantrieb.join()
    Vorderradantrieb.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))

