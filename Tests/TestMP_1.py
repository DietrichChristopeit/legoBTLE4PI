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
from queue import Empty
from random import randint
from time import sleep


class Motor:
    def __init__(self, port: int, execQ: Queue, terminate: Event):
        self._execQ = execQ
        self._terminate: Event = terminate
        self._cvPortFree = Condition()
        self._portFree = Event()
        self._port: int = port
        self._rsltQ: Queue = Queue()

    @property
    def port(self) -> int:
        return self._port

    @property
    def rsltQ(self) -> Queue:
        return self._rsltQ

    def prod(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(name))
        e = None
        while not self._terminate.is_set():
            e = randint(6, 11)
            with self._cvPortFree:
                if not self._execQ.full():
                    print("[{}]-[SND]: PORT: {} - WAITING TO SEND {}".format(name, self._port, e))
                    self._cvPortFree.wait_for(lambda: self._portFree.is_set())
                    if self._terminate.is_set():
                        print("[{}]-[MSG]: PORT: {} - ABORTING COMMAND {}...".format(name, self._port, e))
                        self._portFree.set()
                        self._cvPortFree.notify_all()
                        break
                    self._portFree.clear()
                    print("[{}]-[SND]: PORT: {} - SENDING COMMAND {}".format(name, self._port, e))
                    self._execQ.put((e, self._port))
                    print("[{}]-[SND]: PORT: {} - COMMAND SENT {}".format(name, self._port, e))
                    self._cvPortFree.notify_all()
            sleep(0.0001)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        with self._cvPortFree:
            self._portFree.set()
            self._cvPortFree.notify_all()
        return

    def proc(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(name))
        while not self._terminate.is_set():

            with self._cvPortFree:
                try:
                    m = self._rsltQ.get()
                    if m == 5:
                        print("[{}]-[RCV]: PORT: {} - OK {}...".format(name, self._port, m))
                        self._portFree.set()
                    if m in {3, 6, 7, 8, 9, 10}:
                        print("[{}]-[RCV]: PORT: {} - SETTING CURRENT ANGLE {}...".format(name, self._port, m))
                    if m in {4, 2, 1}:
                        print("[{}]-[RCV]: PORT: {} - ERROR MESSAGE {}...".format(name, self._port, m))
                except Empty:
                    sleep(0.00001)
                finally:
                    self._cvPortFree.notify_all()

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        with self._cvPortFree:
            self._portFree.set()
            self._cvPortFree.notify_all()
        return


class Delegate:

    def __init__(self, cmdQ: Queue, terminate: Event):
        self._cmdQ = cmdQ
        self._terminate: Event = terminate
        self._motors: [Motor] = []

    def register(self, motor: Motor):
        self._motors.append(motor)

    def prod(self, name):
        print("[{}]-[MSG]: STARTED...".format(name))
        while not self._terminate.is_set():
            try:
                c = self._cmdQ.get(timeout=0.01)
                print("[{}]-[RCV]: RECEIVED COMMAND: {}".format(name, c))
            except Empty:
                pass
            e = randint(1, 10)
            p = randint(0, 1)
            for m in self._motors:
                if m.port == p:
                    m.rsltQ.put(e)
                    print("[{}]-[SND]: COMMAND RESULTS SENT {} to PORT {}".format(name, e, m.port))
            sleep(0.0001)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(name))
        return


if __name__ == '__main__':
    execQ = Queue(maxsize=200)
    rsltQ = Queue(maxsize=500)
    cvPortFree: Condition = Condition()
    portFree: Event = Event()
    portFree.set()

    terminate = Event()

    motor1 = Motor(0, execQ, terminate)
    motor2 = Motor(1, execQ, terminate)
    delegate = Delegate(execQ, terminate)
    delegate.register(motor1)
    delegate.register(motor2)

    motorP1 = Process(name="MOTOR1", target=motor1.proc, args=("MOTOR1", ), daemon=True)
    motorP1CMD = Process(name="MOTOR1 COMMAND PRODUCER", args=("MOTOR1 COMMAND PRODUCER", ), target=motor1.prod, daemon=True)
    motorP2 = Process(name="MOTOR2", target=motor2.proc, args=("MOTOR2", ), daemon=True)
    motorP2CMD = Process(name="MOTOR2 COMMAND PRODUCER", target=motor1.prod, args=("MOTOR2 COMMAND PRODUCER", ), daemon=True)
    delegateP = Process(name="DELEGATE", target=delegate.prod, args=("DELEGATE", ), daemon=True)

    motorP1.start()
    motorP1CMD.start()
    motorP2.start()
    motorP2CMD.start()

    delegateP.start()

    sleep(10)

    terminate.set()
    motorP1.join()
    print("{} Exitcode: {}".format(motorP1.name, motorP1.exitcode))
    motorP2.join()
    print("{} Exitcode: {}".format(motorP2.name, motorP2.exitcode))
    motorP2CMD.join()
    motorP1CMD.join()
    delegateP.join()
    print("{} Exitcode: {}".format(delegateP.name, delegateP.exitcode))

    print("{}: SHUT DOWN COMPLETE...".format(__name__))
