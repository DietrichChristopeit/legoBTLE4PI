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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

#
   MIT License
  
   Copyright (c) 2021 Dietrich Christopeit
  
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
  
   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.
  
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
  

#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
import queue
import threading
from random import uniform
from time import sleep
from LegoBTLE.Constants.Port import Port


class Motor(threading.Thread):

    def __init__(self, name: str, anschluss: Port, gearRatio: float = 1.0, execQ: queue.Queue = None,
                 terminateOn: threading.Event = None, debug: bool = False):

        super(Motor, self).__init__()
        self._name: str = name
        self._anschluss: int = anschluss.value
        self._gearRatio: float = gearRatio

        self._execQ: queue.Queue = execQ
        self._rcvQ: queue.Queue = queue.Queue(maxsize=100)
        self._cmdQ: queue.Queue = queue.Queue()

        self._terminate: threading.Event = terminateOn
        self._portFree: threading.Event = threading.Event()
        self._portFree.set()
        self.setDaemon(True)
        self._debug: bool = debug

        self._currentAngle: float = 0.00
        self._previousAngle: float = 0.00
        self._upm: int = 0

    @property
    def nameMotor(self) -> str:
        return self._name

    @property
    def winkelAlt(self) -> float:
        return self._previousAngle

    @property
    def winkelAktuell(self) -> float:
        return self._currentAngle

    @property
    def uebersetzung(self) -> float:
        return self._gearRatio

    @property
    def anschluss(self) -> int:
        return self._anschluss

    @property
    def rcvQ(self) -> queue.Queue:
        return self._rcvQ

    @property
    def portFree(self) -> threading.Event:
        return self._portFree

    def run(self):
        if self._debug:
            print("[{}]-[MSG]: Started...".format(threading.current_thread().getName()))
        receiver = threading.Thread(target=self.receiver, args=(self._terminate,),
                                    name="{} RECEIVER".format(self._name), daemon=True)
        receiver.start()

        self._terminate.wait()
        if self._debug:
            print("[{}]-[SIG]: SHUTTING DOWN...".format(threading.current_thread().getName()))
        receiver.join()
        if self._debug:
            print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def terminate(self):
        self._terminate.set()
        return

    def receiver(self, terminate: threading.Event):
        print("[{}]-[MSG]: Receiver started...".format(threading.current_thread().getName()))

        while not terminate.is_set():
            if self._rcvQ.empty():
                sleep(1.0)
                continue
            result = self._rcvQ.get()
            if result[1] == 0x0a:
                if self._debug:
                    print(
                      "[{}]-[MSG]: freeing port {:02x}...".format(threading.current_thread().getName(), self._anschluss))
                self._portFree.set()
            if self._debug:
                print("[{:02x}]-[MSG]: received result: {:02x}".format(result[0], result[1]))

        print("[{}]-[SIG]: RECEIVER SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def commandA(self, caller):
        if self._debug:
            print("[{}]-[CMD]: WAITING: Port free for COMMAND A".format(caller))
        self._portFree.wait()
        if self._debug:
            print("[{}]-[SIG]: PASS: Port free for COMMAND A".format(caller))
        self._portFree.clear()
        sleep(uniform(0, 5))
        if self._debug:
            self._execQ.put(("[{}]-[CMD]: COMMAND A".format(caller), self._anschluss))
        return

    def commandB(self, caller):
        if self._debug:
            print("[{}]-[CMD]: WAITING: Port free for COMMAND B".format(caller))

        self._portFree.wait()

        if self._debug:
            print("[{}]-[SIG]: PASS: Port free for COMMAND B".format(caller))

        self._portFree.clear()
        sleep(uniform(0, 5))

        if self._debug:
            self._execQ.put(("[{}]-[CMD]: COMMAND B".format(caller), self._anschluss))
        return

    def commandC(self, caller):
        if self._debug:
            print("[{}]-[CMD]: WAITING: Port free for COMMAND C".format(caller))

        self._portFree.wait()

        if self._debug:
            print("[{}]-[SIG]: PASS: Port free for COMMAND C".format(caller))

        self._portFree.clear()
        sleep(uniform(0, 5))
        if self._debug:
            self._execQ.put(("[{}]-[CMD]: COMMAND C".format(caller), self._anschluss))
        return


class HubSimulator(threading.Thread):

    def __init__(self, name: str, execQ: queue.Queue, terminateOn: threading.Event, execQEmpty: threading.Event, debug: bool = False):
        super(HubSimulator, self).__init__()
        self._name = name
        self._execQ = execQ
        self._motors: [Motor] = []

        self._terminate: threading.Event = terminateOn

        self._delegateQ: queue.Queue = queue.Queue()
        self._delegateRES_Q: queue.Queue = queue.Queue()
        self._Delegate: threading.Thread = None

        self._notifierQ: queue.Queue = queue.Queue()
        self._Notifier: threading.Thread = None

        self._execQEmpty = execQEmpty

        self.setDaemon(True)
        self._debug = debug

    def run(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        self._Delegate = threading.Thread(target=self.delegation, args=(self._terminate,), name="Delegate", daemon=True)
        self._Delegate.start()
        self._Notifier = threading.Thread(target=self.notifier, args=(self._terminate,), name="Notifier", daemon=True)
        self._Notifier.start()

        self.execute()

        self._terminate.wait()

        print("[{}]-[SIG]: SHUTTING DOWN...".format(threading.current_thread().getName()))

        self._Delegate.join()
        self._Notifier.join()

        print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def terminate(self):
        self._terminate.set()
        return

    def register(self, motor: Motor):
        self._motors.append(motor)
        if self._debug:
            print("[{}]-[MSG]: REGISTERED {} ...".format(threading.current_thread().getName(), motor.name))
        return

    def execute(self):
        print("[{}]-[MSG]: Execution event_loop STARTED...".format(threading.current_thread().getName()))
        while not self._terminate.is_set():
            if not self._execQ.empty():
                self._execQEmpty.clear()
                command = self._execQ.get()
                self._delegateQ.put(command)
                continue
            self._execQEmpty.set()

        print("[{}]-[MSG]: SHUTDOWN COMPLETE EXEC LOOP ...".format(threading.current_thread().getName()))
        return

    def notifier(self, terminate: threading.Event):
        print("[HUB {}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._notifierQ.get()
            if self._debug:
                print("[HUB {}]-[RCV] = [{}]: UpStreamMessageBuilder received...".format(threading.current_thread().getName(), command[0]))

            for m in self._motors:
                if m.port == command[1]:
                    if not m.port == 0x01:
                        sleep(round(uniform(0, 5), 2))
                    m.rcvQ.put((command[1], 0x0a))
                    if self._debug:
                        print("[HUB {}]-[SND] -> [{}]: Notification sent...".format(threading.current_thread().getName(),
                                                                                m.name))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def delegation(self, terminate: threading.Event):
        print("[HUB {}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._delegateQ.get()
            self._notifierQ.put(command)
            if self._debug:
                print("[HUB {}]-[SND] -> [{}] = [{}]: UpStreamMessageBuilder sent...".format(threading.current_thread().getName(), self._Notifier.name, command[0]))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return


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


    hub: HubSimulator = HubSimulator("HubSimulator", execQ=init()[0], terminateOn=init()[1],
                                     execQEmpty=init()[2])

    motorA: Motor = Motor("Motor A", anschluss=Port.A, execQ=init()[0], terminateOn=init()[1])
    motorB: Motor = Motor("Motor B", anschluss=Port.B, execQ=init()[0], terminateOn=init()[1])
    motorC: Motor = Motor("Motor C", anschluss=Port.C, execQ=init()[0], terminateOn=init()[1])

    # Fahrtprogramm
    print("[{}]-[MSG]: Starting UpStreamMessageBuilder Execution Subsystem...".format(init()[3].name))
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
    print("Sending payload A to Motor A")
    motorA.commandA(motorA.name)
    print("Sending payload B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending payload A to Motor B")
    motorB.commandA(motorB.name)
    print("Sending payload C to Motor B")
    motorB.commandC(motorB.name)
    print("Sending payload B to Motor A")
    motorA.commandB(motorA.name)
    print("[{}]-[SIG]: WAITING FOR ALL COMMANDS TO END...".format(init()[3].name))
    init()[2].wait()
    print("[{}]-[SIG]: RESUME COMMAND EXECUTION RECEIVED...".format(init()[3].name))
    print("Sending payload C to Motor A")
    motorA.commandC(motorA.name)
    print("Sending payload B to Motor B")
    motorB.commandB(motorB.name)
    print("Sending payload B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending payload B to Motor A")
    motorA.commandB(motorA.name)

    print("[{}]-[MSG]: SHUTTING DOWN...".format(init()[3].name))
    sleep(2)
    init()[1].set()
    print("[{}]-[SIG]: SHUT DOWN SIGNAL SENT...".format(init()[3].name))
    motorC.join()
    motorB.join()
    motorA.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: UpStreamMessageBuilder Execution Subsystem ...".format(init()[3].name))
    # print("[{}]-[MSG]: SHUTTING DOWN: UpStreamMessageBuilder Execution Subsystem...".format(mainThread.name))
    # sleep(2)
    # terminateEvent.set()
    #
    # motorC.join()
    # motorB.join()
    # motorA.join()
    # print("[{}]-[MSG]: SHUT DOWN COMPLETE: UpStreamMessageBuilder Execution Subsystem ...".format(mainThread.name))
