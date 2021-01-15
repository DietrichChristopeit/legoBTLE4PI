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
from random import uniform
from time import sleep


class Motor(threading.Thread):

    def __init__(self, name: str, port: int, execQ: queue.Queue, terminate: threading.Event):

        super(Motor, self).__init__()
        self._name: str = name
        self._port: int = port
        self._execQ: queue.Queue = execQ
        self._rcvQ: queue.Queue = queue.Queue(maxsize=100)
        self._cmdQ: queue.Queue = queue.Queue()

        self._terminate: threading.Event = terminate
        self._portFree: threading.Event = threading.Event()
        self._portFree.set()
        self.setDaemon(True)

    @property
    def name(self) -> str:
        return self._name

    @property
    def rcvQ(self) -> queue.Queue:
        return self._rcvQ

    @property
    def port(self) -> int:
        return self._port

    @property
    def portFree(self) -> threading.Event:
        return self._portFree

    def run(self):
        print("[{}]-[MSG]: Started...".format(threading.current_thread().getName()))
        # executor = threading.Thread(target=self.execute(), name=self._name)
        receiver = threading.Thread(target=self.receiver, args=(self._terminate,), name="{} RECEIVER".format(self._name), daemon=True)
        # executor.start()
        receiver.start()

        self._terminate.wait()
        print("[{}]-[SIG]: SHUTTING DOWN...".format(threading.current_thread().getName()))
        receiver.join()
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
                print("[{}]-[MSG]: freeing port {:02x}...".format(threading.current_thread().getName(), self._port))
                self._portFree.set()
            print("[{:02x}]-[MSG]: received result: {:02x}".format(result[0], result[1]))

        print("[{}]-[SIG]: RECEIVER SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def commandA(self, caller):
        print("[{}]-[CMD]: WAITING: port free for COMMAND A".format(caller))
        self._portFree.wait()
        print("[{}]-[SIG]: PASS: port free for COMMAND A".format(caller))
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND A".format(caller), self._port))
        return

    def commandB(self, caller):
        print("[{}]-[CMD]: WAITING: port free for COMMAND B".format(caller))
        self._portFree.wait()
        print("[{}]-[SIG]: PASS: port free for COMMAND B".format(caller))
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND B".format(caller), self._port))
        return

    def commandC(self, caller):
        print("[{}]-[CMD]: WAITING: port free for COMMAND C".format(caller))
        self._portFree.wait()
        print("[{}]-[SIG]: PASS: port free for COMMAND C".format(caller))
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND C".format(caller), self._port))
        return


class HubSimulator(threading.Thread):

    def __init__(self, name: str, execQ: queue.Queue, terminate: threading.Event, execQEmpty: threading.Event):
        super(HubSimulator, self).__init__()
        self._name = name
        self._execQ = execQ
        self._motors: [Motor] = []
        self._terminate: threading.Event = terminate
        self._delegateQ: queue.Queue = queue.Queue()
        self._delegateRES_Q: queue.Queue = queue.Queue()
        self._Delegate: threading.Thread = None
        self._notifierQ: queue.Queue = queue.Queue()
        self._Notifier: threading.Thread = None
        self._execQEmpty = execQEmpty
        self.setDaemon(True)

    def run(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        self._Delegate = threading.Thread(target=self.delegation, args=(self._terminate, ), name="Delegate", daemon=True)
        self._Delegate.start()
        self._Notifier = threading.Thread(target=self.notifier, args=(self._terminate, ), name="Notifier", daemon=True)
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
        print("[{}]-[MSG]: REGISTERED {} ...".format(threading.current_thread().getName(), motor.name))
        return

    def execute(self):
        print("[{}]-[MSG]: Execution loop STARTED...".format(threading.current_thread().getName()))
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
            print("[HUB {}]-[RCV] = [{}]: Command received...".format(threading.current_thread().getName(), command[0]))
            for m in self._motors:
                if m.port == command[1]:
                    if not m.port == 0x01:
                        sleep(round(uniform(0, 5), 2))
                    m.rcvQ.put((command[1], 0x0a))
                    print("[HUB {}]-[SND] -> [{}]: Notification sent...".format(threading.current_thread().getName(), m.name))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def delegation(self, terminate: threading.Event):
        print("[HUB {}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._delegateQ.get()
            self._notifierQ.put(command)
            print("[HUB {}]-[SND] -> [{}] = [{}]: Command sent...".format(threading.current_thread().getName(),
                                                                      self._Notifier.name, command[0]))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return


if __name__ == '__main__':
    terminateEvent: threading.Event = threading.Event()

    mainThread = threading.current_thread()
    mainThread.setName("MAIN")

    hubExecQ: queue.Queue = queue.Queue(maxsize=100)
    hubExecQEmptyEvent: threading.Event = threading.Event()
    hub: HubSimulator = HubSimulator("HubSimulator", hubExecQ, terminateEvent, hubExecQEmptyEvent)

    motorA: Motor = Motor("Motor A", 0x00, hubExecQ, terminateEvent)
    motorB: Motor = Motor("Motor B", 0x01, hubExecQ, terminateEvent)
    motorC: Motor = Motor("Motor C", 0x02, hubExecQ, terminateEvent)

    print("[{}]-[MSG]: Starting Command Execution Subsystem...".format(mainThread.name))
    hub.start()
    motorA.start()
    motorC.start()
    motorB.start()
    print("[{}]-[MSG]: Registering Motor Devices...".format(mainThread.name))
    hub.register(motorB)
    hub.register(motorC)
    hub.register(motorA)
    print("[{}]-[MSG]: waiting 5...".format(mainThread.name))
    sleep(5)
    print("Sending command A to Motor A")
    motorA.commandA(motorA.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending command A to Motor B")
    motorB.commandA(motorB.name)
    print("Sending command C to Motor B")
    motorB.commandC(motorB.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("[{}]-[SIG]: WAITING FOR ALL COMMANDS TO END...".format(mainThread.name))
    hubExecQEmptyEvent.wait()
    print("[{}]-[SIG]: RESUME COMMAND EXECUTION RECEIVED...".format(mainThread.name))
    print("Sending command C to Motor A")
    motorA.commandC(motorA.name)
    print("Sending command B to Motor B")
    motorB.commandB(motorB.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)
    print("Sending command B to Motor A")
    motorA.commandB(motorA.name)

    print("[{}]-[MSG]: SHUTTING DOWN...".format(mainThread.name))
    sleep(2)
    terminateEvent.set()
    print("[{}]-[SIG]: SHUT DOWN SIGNAL SENT...".format(mainThread.name))
    motorC.join()
    motorB.join()
    motorA.join()
    print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))
    # print("[{}]-[MSG]: SHUTTING DOWN: Command Execution Subsystem...".format(mainThread.name))
    # sleep(2)
    # terminateEvent.set()
    #
    # motorC.join()
    # motorB.join()
    # motorA.join()
    # print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))


