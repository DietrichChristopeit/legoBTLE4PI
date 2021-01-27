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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

from multiprocessing import Process, Queue, Event
from random import uniform
from time import sleep


class Proctest(Process):
    def __init__(self, name: str, terminate: Event, q: Queue):
        super().__init__()
        self._name = name
        self._q = q
        self.terminate = terminate
        return

    def run(self):
        while not self.terminate.is_set():
            print("Name: {}:{}".format(Process.name, self._name))
            if not self._q.qsize() == 0:
                print("Queue: {}".format(self._q.get()))
            sleep(uniform(1, 3))

        print("Shutting down...")
        return


if __name__ == "__main__":
    terminate: Event = Event()
    q: Queue = Queue()
    p: Proctest = Proctest("TESTPROCESS", terminate, q)

    p.start()

    for i in range(1, 10):
        print("MAIN: putting {}".format(i))
        q.put(i)
        sleep(0.5)

    sleep(20)

    terminate.set()
    p.join()
