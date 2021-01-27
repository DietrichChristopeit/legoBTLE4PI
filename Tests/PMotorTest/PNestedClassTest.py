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

from multiprocessing import Process, Event
from time import sleep


class Outer:
    def __init__(self, maxIterations: int = 0, terminate: Event = None):
        self._maxIterations = maxIterations
        self._inner = self.Inner(maxIterations)
        self._terminate: Event = terminate
        return
        
    class Inner:
        def __init__(self, maxIterations: int = 0):
            self._maxIterations = maxIterations
            return
        
        def loop(self, out: int):
            for i in range(0, self._maxIterations):
                print("Iteration INNER: {}:{}".format(out, i))
                sleep(.01)
            return
        
    def loopOuter(self):
        for i in range(0, self._maxIterations):
            print("Iteration OUTER: {}".format(i))
            self._inner.loop(i)
            sleep(.02)
        self._terminate.set()
        return

    def loopOuter1(self):
        for i in range(self._maxIterations, 0, -1):
            print("Iteration OUTER 1: {}".format(i))
            self._inner.loop(i)
            sleep(.03)
        self._terminate.set()
        return


if __name__ == '__main__':
    terminate: Event = Event()
    outer: Outer = Outer(20, terminate)
    
    p: Process = Process(name="Outer Process", target=outer.loopOuter, daemon=True)
    p1: Process = Process(name = "Outer Process", target = outer.loopOuter1, daemon = True)
    p.start()
    p1.start()
    terminate.wait()
    p.join()
    p1.join()
    print("MAIN: SHUTDOWN")
    

