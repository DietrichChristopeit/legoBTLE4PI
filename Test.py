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
        
        receiver.join()
        print("[{}]-[MSG]: Shutting down...".format(threading.current_thread().getName()))
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
                self._portFree.set()
            print("[{:02x}]-[MSG]: received result: {:02x}".format(result[0], result[1]))
        print("[{}]-[MSG]: Receiver shutting down...".format(threading.current_thread().getName()))
        return

    def commandA(self):
        self._portFree.wait()
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND A".format(threading.current_thread().getName()), self._port))
        return

    def commandB(self):
        self._portFree.wait()
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND B".format(threading.current_thread().getName()), self._port))
        return

    def commandC(self):
        self._portFree.wait()
        self._portFree.clear()
        sleep(uniform(0, 5))
        self._execQ.put(("[{}]-[CMD]: COMMAND C".format(threading.current_thread().getName()), self._port))
        return


class HubSimulator(threading.Thread):

    def __init__(self, name: str, execQ: queue.Queue, terminate: threading.Event):
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

    def run(self):
        self._Delegate = threading.Thread(target=self.delegation, args=(self._terminate, ), name="Delegate", daemon=True)
        self._Delegate.start()
        self._Notifier = threading.Thread(target=self.notifier, args=(self._terminate, ), name="Notifier", daemon=True)
        self._Notifier.start()

        self.execute()
        
        self._terminate.wait()

        self._Delegate.join()
        self._Notifier.join()
        print("[{}]-[MSG]: shutting down...".format(threading.current_thread().getName()))
        return

    def terminate(self):
        self._terminate.set()
        return

    def register(self, motor: Motor):
        self._motors.append(motor)
        return

    def execute(self):
        print("[{}]-[MSG]: Execution loop STARTED...".format(threading.current_thread().getName()))
        while not self._terminate.is_set():
            if not self._execQ.empty():
                command = self._execQ.get()
                self._delegateQ.put(command)
            sleep(1.0)
        
        print("[{}]-[MSG]: Execution loop ENDED...".format(threading.current_thread().getName()))
        return

    def notifier(self, terminate: threading.Event):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._notifierQ.get()
            print("[{}]-[RCV] = [{}]: Command received...".format(threading.current_thread().getName(), command[0]))
            sleep(round(uniform(0, 5), 2))
            for m in self._motors:
                if m.port == command[1]:
                    m.rcvQ.put((command[1], 0x0a))
                    print("[{}]-[SND] -> [{}]: Notification sent...".format(threading.current_thread().getName(), m.name))

        print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().getName()))
        return

    def delegation(self, terminate: threading.Event):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._delegateQ.get()
            self._notifierQ.put(command)
            print("[{}]-[SND] -> [{}] = [{}]: Command sent...".format(threading.current_thread().getName(),
                                                                      self._Notifier.name, command[0]))

        print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().getName()))
        return


if __name__ == '__main__':
    terminateEvent = threading.Event()
    mainThread = threading.current_thread()
    mainThread.setName("MAIN")

    hubExecQ: queue.Queue = queue.Queue(maxsize=100)
    hub: HubSimulator = HubSimulator("HubSimulator", hubExecQ, terminateEvent)
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
    sleep(10)
    print("Sending command A")
    motorA.commandA()
    motorA.commandB()
    motorA.commandB()
    motorA.commandB()
    motorA.commandB()
    motorB.commandC()
    motorA.commandB()
    # print("[{}]-[MSG]: SHUTTING DOWN: Command Execution Subsystem...".format(mainThread.name))
    # sleep(2)
    # terminateEvent.set()
    #
    # motorC.join()
    # motorB.join()
    # motorA.join()
    # print("[{}]-[MSG]: SHUT DOWN COMPLETE: Command Execution Subsystem ...".format(mainThread.name))


