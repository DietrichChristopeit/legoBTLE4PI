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

from multiprocessing import Process, Value, Array, Queue, Event
from random import uniform
from time import sleep


class Producer:

    def __init__(self, execQ: Queue, terminate: Event):
        self._execQ = execQ
        self._terminate: Event = terminate

    def prod(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            e = uniform(1, 2000)
            self._execQ.put(e)
            print("[{}]-[SND]: SENT {}".format(Process.name, e))

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        return


class Receiver:

    def __init__(self, execQ: Queue, terminate: Event):
        self._execQ = execQ
        self._procQ = Queue(maxsize=200)
        self._terminate: Event = terminate

    def rec(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            cmd = self._execQ.get()
            print("[{}]-[RCV]: RECEIVED {}...".format(Process.name, cmd))
            self._procQ.put(cmd)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        return

    def proc(self):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        while not self._terminate.is_set():
            m = self._procQ.get()
            if m > 800:
                print("[{}]-[RCV]: RECEIVED {}...".format(Process.name, m))
            else:
                print("[{}]-[RCV]: DISCARDED {}...".format(Process.name, m))

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        return


if __name__ == '__main__':
    execQ = Queue(maxsize=200)
    terminate = Event()
    producer = Producer(execQ, terminate)
    receiver = Receiver(execQ, terminate)
    rec1 = Receiver(execQ, terminate)
    p = Process(name="PRODUCER", target=producer.prod)
    r = Process(name="RECEIVER", target=receiver.rec)
    r1 = Process(name="RECEIVER", target=receiver.proc)

    p.start()
    r.start()
    r1.start()

    sleep(5)

    terminate.set()
    p.join()
    r.join()
    r1.join()
    print("SHUT DOWN COMPLETE...")
