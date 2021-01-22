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

from multiprocessing import Process, Queue, Event, Condition
from random import randint
from time import sleep


class Motor:
    def __init__(self, port: int, execQ: Queue, terminate: Event):
        self._execQ = execQ
        self._terminate: Event = terminate
        self._cvPortFree = Condition()
        self._portFree = Event()
        self._portFree.set()
        self._port: int = port
        self._rsltQ: Queue = Queue()
        self._procStarted: Event = Event()
        self._prodStarted: Event = Event()

    @property
    def port(self) -> int:
        return self._port

    @property
    def procStarted(self) -> Event:
        return self._procStarted

    @property
    def prodStarted(self) -> Event:
        return self._prodStarted

    @property
    def rsltQ(self) -> Queue:
        return self._rsltQ

    def prod(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(name))
        e = None
        self._prodStarted.set()
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            e = randint(20, 30)
            with self._cvPortFree:
                print("[{}]-[SND]: PORT: {} - WAITING TO SEND {}".format(name, self._port, (e, self._port)))
                self._cvPortFree.wait_for(lambda: self._portFree.is_set() or self._terminate.is_set())
                if self._terminate.is_set():
                    print("[{}]-[MSG]: PORT: {} - ABORTING COMMAND {}...".format(name, self._port, (e, self._port)))
                    self._portFree.set()
                    self._cvPortFree.notify_all()
                    break
                self._portFree.clear()
                print("[{}]-[SND]: PORT: {} - SENDING COMMAND {}".format(name, self._port, (e, self._port)))
                self._execQ.put((e, self._port))
                print("[{}]-[SND]: PORT: {} - COMMAND SENT {}".format(name, self._port, (e, self._port)))
                self._cvPortFree.notify_all()
            # sleep(.001)  # to make sending and receiving (port freeing) more evenly distributed

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        with self._cvPortFree:
            self._portFree.set()
            self._cvPortFree.notify_all()
        self._prodStarted.clear()
        return

    def proc(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(name))
        self._procStarted.set()
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break

            with self._cvPortFree:
                if self._terminate.is_set():
                    self._portFree.set()
                    self._cvPortFree.notify_all()
                    break
                if not self._rsltQ.qsize() == 0:
                    m = self._rsltQ.get()
                    if m == 5:
                        print("[{}]-[RCV]: PORT: {} - OK {}...".format(name, self._port, m))
                        self._portFree.set()
                    if m in {3, 6, 7, 8, 9, 10}:
                        print("[{}]-[RCV]: PORT: {} - SETTING CURRENT ANGLE {}...".format(name, self._port, m))
                    if m in {4, 2, 1}:
                        print("[{}]-[RCV]: PORT: {} - ERROR MESSAGE {}...".format(name, self._port, m))

                if self._terminate.is_set():
                    self._portFree.set()
                    self._cvPortFree.notify_all()
                    break
                self._cvPortFree.notify_all()
            # sleep(.001)  # to make sending and receiving (port freeing) more evenly distributed

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        self._portFree.set()
        self.procStarted.clear()
        return


class Delegate:

    def __init__(self, cmdQ: Queue, terminate: Event):
        self._cmdQ = cmdQ
        self._terminate: Event = terminate
        self._motors: [Motor] = []
        self._delegateStarted: Event = Event()

    @property
    def delegateStarted(self) -> Event:
        return self._delegateStarted

    def register(self, motor: Motor):
        self._motors.append(motor)

    def prod(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(name))
        self._delegateStarted.set()
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break

            if not self._cmdQ.qsize() == 0:
                c = self._cmdQ.get()
                print("[{}]-[RCV]: RECEIVED COMMAND: {}".format(name, c))

            e = randint(1, 10)
            p = randint(0, 1)
            for m in self._motors:
                if m.port == p:
                    m.rsltQ.put(e)
                    print("[{}]-[SND]: COMMAND RESULTS SENT {} to PORT {}".format(name, e, m.port))
            # sleep(.001)  # to make sending and receiving (port freeing) more evenly distributed

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        self._delegateStarted.clear()
        return


if __name__ == '__main__':
    execQ = Queue(maxsize=200)

    terminate: Event = Event()

    motor0 = Motor(0, execQ, terminate)

    motor1 = Motor(1, execQ, terminate)

    delegate = Delegate(execQ, terminate)
    delegate.register(motor0)
    delegate.register(motor1)

    motorP0 = Process(name="MOTOR0", target=motor0.proc, args=("PROC_essor: MOTOR0",), daemon=False)
    motorP0CMD = Process(name="MOTOR0 COMMAND PRODUCER", args=("PROD_ucer: MOTOR0",), target=motor0.prod, daemon=False)
    motorP1 = Process(name="MOTOR1", target=motor1.proc, args=("PROC_essor: MOTOR1",), daemon=False)
    motorP1CMD = Process(name="MOTOR1 COMMAND PRODUCER", target=motor1.prod, args=("PROD_ucer: MOTOR1",), daemon=False)
    delegateP = Process(name="DELEGATE", target=delegate.prod, args=("BTLE DELEGATE", ), daemon=False)

    delegateP.start()
    delegate.delegateStarted.wait()

    motorP0.start()
    motor0.procStarted.wait()
    motorP0CMD.start()
    motor0.prodStarted.wait()

    motorP1.start()
    motor1.procStarted.wait()
    motorP1CMD.start()
    motor1.prodStarted.wait()



    sleep(2)

    terminate.set()
    delegateP.join()
    print("[{}]-[MSG]: SHUT DOWN - EXITCODE: {}...".format(delegateP.name, delegateP.exitcode))
    motorP0.join()
    print("[{}]-[MSG]: SHUT DOWN - EXITCODE: {}...".format(motorP0.name, motorP0.exitcode))
    motorP1.join()
    print("[{}]-[MSG]: SHUT DOWN - EXITCODE: {}...".format(motorP1.name, motorP1.exitcode))
    motorP1CMD.join()
    print("[{}]-[MSG]: SHUT DOWN - EXITCODE: {}...".format(motorP1CMD.name, motorP1CMD.exitcode))
    motorP0CMD.join()
    print("[{}]-[MSG]: SHUT DOWN - EXITCODE: {}...".format(motorP0CMD.name, motorP0CMD.exitcode))

    print("{}: SHUT DOWN COMPLETE...".format(__name__))
