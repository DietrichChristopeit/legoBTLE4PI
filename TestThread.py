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


class TestThread(threading.Thread):

    def __init__(self, x: int, z: str, t: float, event: threading.Event, q: queue.Queue, cel: threading.Event, setDeamon: bool = False):
        super().__init__()
        if setDeamon:
            self.setDaemon(True)
        self._x = x
        self._v = "test"
        self._z = z
        self._t = t
        self._terminate = event
        self._suspend = threading.Event()
        self._cel = cel
        self._mExec = threading.Event()
        self._mExec.set()
        self._q = q
        self._wait = False
        return

    def exec(self, i: int, w: bool = False):
        if w:
            self._wait = True
            self._cel.clear()
        print("{} / loading {}".format(self._z, i))
        self._q.put(i)
        return

    def printSomething(self, j: int):
        #print(self._z, "Checking Command Execution Lock...")
        #self._cel.wait()
        #self._mExec.wait()
        #self._mExec.clear()
        for i in range(10):
            print("{} / ZAHL: {} + {}".format(self._z, j, i))
            sleep(.5)
        if self._wait:
            self._cel.set()
        return

    def suspend(self, suspend: bool = True):
        if not suspend:
            print("wakeup call")
            self._suspend.set()
        else:
            print("suspending")
            self._suspend.clear()
        return

    @property
    def z(self) -> str:
        return self._z

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int):
        self._x = value
        return

    def do_somethingForT(self, t: float):
        print(self._z, "is doing something")
        sleep(t)
        print(self._z, "finished...")
        return

    def run(self):
        print("starting", self._z)
        self._suspend.set()
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            self._suspend.wait()

            while not self._q.empty():
                self.printSomething(self._q.get())

        print(self._z, "exiting...")
        return


if __name__ == '__main__':
    tTerminate = threading.Event()
    uTerminate = threading.Event()
    q = queue.Queue()
    r = queue.Queue()
    cel = threading.Event()
    cel.set()
    t = TestThread(5, "THREAD T", 0.5, tTerminate, q, cel)
    u = TestThread(5, "THREAD U", 0.5, uTerminate, r, cel)
    t.start()
    u.start()
    t.exec(1, True)
    cel.wait()
    t.exec(2)
    t.exec(3)
    u.exec(1)

    u.exec(2)

    u.exec(3)

    sleep(2)
    tTerminate.set()
    uTerminate.set()
    t.join()
    u.join()
    print("ABOUT TO TERMINATE...")
    t.join()
    u.join()
    print("TERMINATED")
    print("exit")


