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
import threading
from time import sleep


class TestThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setName("TestThread")
        self.setDaemon(True)
        self._selfTerminate: threading.Event = threading.Event()
        self._terminate: threading.Event = threading.Event()
        self._terminateCondition: threading.Condition = threading.Condition()

        self._firstDelegateStartedEvent: threading.Event = threading.Event()
        self._secondDelegateStartedEvent: threading.Event = threading.Event()
        self._delegateCondition: threading.Condition = threading.Condition()
        self._fdelegateThread: threading.Thread = threading.Thread(target=self.Testdelegate,
                                                                   args=(self._firstDelegateStartedEvent,),
                                                                   name="FIRST TESTDELEGATE THREAD", daemon=True)
        self._sdelegateThread: threading.Thread = threading.Thread(target=self.Testdelegate,
                                                                   args=(self._secondDelegateStartedEvent,),
                                                                   name="SECOND TESTDELEGATE THREAD", daemon=True)

    @property
    def selfTerminate(self) -> threading.Event:
        return self._selfTerminate

    def run(self):

        print("[{}]-[MSG]: STARTING FIRST DELEGATE THREAD...".format(threading.current_thread().name))
        self._fdelegateThread.start()
        print("[{}]-[MSG]: Waiting for FIRST DELEGATE THREAD...".format(threading.current_thread().name))
        self._firstDelegateStartedEvent.wait()
        print("[{}]-[MSG]: FIRST DELEGATE THREAD STARTED...".format(threading.current_thread().name))
        print("[{}]-[MSG]: STARTING SECOND DELEGATE THREAD...".format(threading.current_thread().name))
        self._sdelegateThread.start()
        print("[{}]-[MSG]: Waiting for SECOND DELEGATE THREAD...".format(threading.current_thread().name))
        self._secondDelegateStartedEvent.wait()
        print("[{}]-[MSG]: SECOND DELEGATE THREAD STARTED...".format(threading.current_thread().name))
        print("THREADS: {}".format(threading.enumerate()))

        print("Waiting for 10")
        sleep(10)
        self._terminate.set()
        print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().name))
        print("[{}]-[MSG]: SHUTTING DOWN: DELEGATE THREADS...".format(threading.current_thread().name))
        self._fdelegateThread.join()
        print("[{}]-[MSG]: FIRST DELEGATE THREAD DOWN...".format(threading.current_thread().name))
        self._sdelegateThread.join()
        print("[{}]-[MSG]: SECOND DELEGATE THREAD DOWN...".format(threading.current_thread().name))
        print("[{}]-[MSG]: SHUT DOWN DELEGATE THREADS COMPLETE...".format(threading.current_thread().name))
        print("THREADS: {}".format(threading.enumerate()))

        print("[{}]-[MSG]: SHUT DOWN COMPLETE...".format(threading.current_thread().name))
        self._selfTerminate.set()

    def Testdelegate(self, delegateStartedEvent: threading.Event):

        delegateStartedEvent.set()
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().name))

        while not self._terminate.is_set():
            print("[{}]-[MSG]: ALIVE...".format(threading.current_thread().name))
            sleep(0.2)

        delegateStartedEvent.clear()
        print("[{}]-[MSG]: SHUT DOWN COMPLETE...".format(threading.current_thread().name))
        return


if __name__ == '__main__':

    testThread: TestThread = TestThread()
    testThread.start()
    print("THREADS: {}".format(threading.enumerate()))
    t = testThread.selfTerminate.wait()
    print("THREADS: {}".format(threading.enumerate()))
    print("EXIT")
