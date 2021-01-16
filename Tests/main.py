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

if __name__ == '__main__':
    def init():
        # BEGINN Initialisierung
        terminateEvent: threading.Event = threading.Event()

        mainThread = threading.current_thread()
        mainThread.setName("MAIN")

        hubExecQ: queue.Queue = queue.Queue(maxsize=100)
        hubExecQEmptyEvent: threading.Event = threading.Event()
        # ENDE Initialisierung
        return hubExecQ, terminateEvent, hubExecQEmptyEvent, mainThread


    hub: Hub = Hub("Lego Hub 2.0", execQ=init()[0], terminateOn=init()[1],
                   execQEmpty=init()[2])

    motorA: SingleMotor = SingleMotor("Motor A", port=Port.A, execQ=init()[0], terminateOn=init()[1])
    motorB: SingleMotor = SingleMotor("Motor B", port=Port.B, execQ=init()[0], terminateOn=init()[1])
    motorC: SingleMotor = SingleMotor("Motor C", port=Port.C, execQ=init()[0], terminateOn=init()[1])

    # Fahrtprogramm
    print("[{}]-[MSG]: Starting Command Execution Subsystem...".format(init()[3].name))
    hub.start()
    motorA.start()
    motorC.start()
    motorB.start()
    print("[{}]-[MSG]: Registering Motor Devices...".format(init()[3].name))
    hub.register(motorB)
    hub.register(motorC)
    hub.register(motorA)
    print("[{}]-[MSG]: waiting 5...".format(init()[3].name))
    sleep(5)
    motorA.reset()
    motorB.reset()
    motorC.reset()
    print("Sending data A to Motor A")
    motorA.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data B to Motor A")
    motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data A to Motor B")
    motorB.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data C to Motor B")
    motorB.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data B to Motor A")
    motorB.turnForDegrees(50, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("[{}]-[SIG]: WAITING FOR ALL COMMANDS TO END...".format(init()[3].name))
    init()[2].wait()
    print("[{}]-[SIG]: RESUME COMMAND EXECUTION RECEIVED...".format(init()[3].name))
    print("Sending data C to Motor A")
    motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data B to Motor B")
    motorB.turnForDegrees(50, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.BREAK, withFeedback=True)
    print("Sending data B to Motor A")
    motorA.turnForT(2560, MotorConstant.BACKWARD, power=80, finalAction=MotorConstant.HOLD, withFeedback=True)
    print("Sending data B to Motor A")
    motorA.turnForT(2560, MotorConstant.FORWARD, power=80, finalAction=MotorConstant.COAST, withFeedback=True)

    print("[{}]-[MSG]: SHUTTING DOWN...".format(init()[3].name))
    sleep(2)
    init()[1].set()
    print("[{}]-[SIG]: SHUT DOWN SIGNAL SENT...".format(init()[3].name))
    motorC.join()
    motorB.join()
    motorA.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(init()[3].name))
    # print("[{}]-[MSG]: SHUTTING DOWN: Command Execution Subsystem...".format(mainThread.name))
    # sleep(2)
    # terminateEvent.set()
    #
    # motorC.join()
    # motorB.join()
    # motorA.join()
    # print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))
