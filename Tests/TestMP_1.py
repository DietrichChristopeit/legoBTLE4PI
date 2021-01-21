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

from multiprocessing import Process, Value, Array, Queue, Event, Condition
from queue import Empty
from random import uniform, randint
from time import sleep


class Commander:
    def __init__(self, execQ: Queue, terminate: Event, cvPortFree: Condition, portFree: Event):
        self._execQ = execQ
        self._terminate: Event = terminate
        self._cvPortFree = cvPortFree
        self._cvPortFree1: Condition = Condition()
        self._portFree = portFree

    def prod(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            e = randint(6, 11)
            print("[{}]-[SND]: WAITING TO SEND {}".format(Process.name, e))
            with self._cvPortFree:
                self._cvPortFree.wait_for(lambda: self._portFree.is_set())
                self._portFree.clear()
                self._execQ.put(e)
                print("[{}]-[SND]: COMMAND SENT {}".format(Process.name, e))
                self._cvPortFree.notify_all()
            sleep(0.0001)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        return


class Delegate:

    def __init__(self, cmdQ: Queue, rsltQ: Queue, terminate: Event):
        self._cmdQ = cmdQ
        self._rsltQ = rsltQ
        self._terminate: Event = terminate

    def prod(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            try:
                c = self._cmdQ.get(timeout=0.01)
                print("[{}]-[RCV]: RECEIVED COMMAND: {}".format(Process.name, c))
            except Empty:
                pass
            e = randint(1, 5)
            self._rsltQ.put(e)
            print("[{}]-[SND]: ANSWER SENT {}".format(Process.name, e))
            sleep(0.0001)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        return


class Receiver:

    def __init__(self, rsltQ: Queue, terminate: Event, cvPortFree: Condition, portFree: Event):
        self._rsltQ = rsltQ
        self._terminate: Event = terminate
        self._cvPortFree = cvPortFree
        self._portFree = portFree
        self._portFree.set()

    def proc(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            if self._rsltQ.empty():
                sleep(0.001)
                continue

            m = self._rsltQ.get()
            with self._cvPortFree:
                if m == 5:
                    print("[{}]-[RCV]: OK {}...".format(Process.name, m))
                    self._portFree.set()
                if not m == 5:
                    print("[{}]-[RCV]: OCCUPIED {}...".format(Process.name, m))
                self._cvPortFree.notify_all()

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        with self._cvPortFree:
            self._portFree.set()
            self._cvPortFree.notify_all()
        return


if __name__ == '__main__':
    execQ = Queue(maxsize=200)
    rsltQ = Queue(maxsize=500)
    cvPortFree: Condition = Condition()
    portFree: Event = Event()
    portFree.set()

    terminate = Event()
    commander = Commander(execQ, terminate, cvPortFree, portFree)
    delegate = Delegate(execQ, rsltQ, terminate)
    receiver = Receiver(rsltQ, terminate, cvPortFree, portFree)
    c = Process(name="COMMANDER", target=commander.prod)
    d = Process(name="DELEGATE", target=delegate.prod)
    r = Process(name="RECEIVER", target=receiver.proc)

    c.start()
    d.start()
    r.start()

    sleep(30)

    terminate.set()
    c.join()
    d.join()
    r.join()
    print("SHUT DOWN COMPLETE...")
