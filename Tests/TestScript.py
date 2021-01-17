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
import queue
import threading
from time import sleep

from LegoBTLE.Constants.MotorConstant import MotorConstant
from LegoBTLE.Constants.Port import Port
from LegoBTLE.Controller.Hub import Hub
from LegoBTLE.Device.Motor import SingleMotor

if __name__=='__main__':
    # BEGINN Initialisierung
    terminateEvent: threading.Event = threading.Event()

    mainThread = threading.current_thread()
    mainThread.setName("MAIN")

    hubExecQ: queue.Queue = queue.Queue(maxsize=100)
    hubExecQEmptyEvent: threading.Event = threading.Event()
    # ENDE Initialisierung

    hub: Hub = Hub(address='90:84:2B:5E:CF:1F', execQ=hubExecQ, terminateOn=terminateEvent,
                   execQEmpty=hubExecQEmptyEvent, debug=True)
    print("[{}]-[MSG]: Starting Command Execution Subsystem...".format(mainThread))
    hub.start()

    Vorderradantrieb: SingleMotor = SingleMotor("Vorderradantrieb", port=Port.A, gearRatio=2.67, execQ=hubExecQ, terminateOn=terminateEvent, debug=True)
    Hinterradantrieb: SingleMotor = SingleMotor("Hinterradantrieb", port=Port.B, gearRatio=2.67, execQ=hubExecQ, terminateOn=terminateEvent)
    Lenkung: SingleMotor = SingleMotor("Lenkung", port=Port.C, gearRatio=2.67, execQ=hubExecQ, terminateOn=terminateEvent)

    # Fahrtprogramm

    Vorderradantrieb.start()
    # motorC.start()
    # motorB.start()
    print("[{}]-[MSG]: Registering Motor Devices...".format(mainThread.name))
    # hub.register(motorB)
    # hub.register(motorC)
    hub.register(Vorderradantrieb)
    print("[{}]-[MSG]: waiting 15...".format(mainThread.name))
    sleep(15)
    # motorA.reset()
    # motorB.reset()
    # motorC.reset()
    print("Sending data TURN to Motor A")
    gradAmAnfang = Vorderradantrieb.currentAngle
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
    Hinterradantrieb.turnForDegrees(3600, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
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

    # terminateEvent.set()
    print("[{}]-[SIG]: SHUT DOWN SIGNAL SENT...".format(mainThread.name))
    # motorC.join()
    # motorB.join()
    Vorderradantrieb.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))
    # print("[{}]-[MSG]: SHUTTING DOWN: Command Execution Subsystem...".format(mainThread.name))
    # sleep(2)
    # terminateEvent.set()
    #
    # motorC.join()
    # motorB.join()
    # motorA.join()
    # print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))
