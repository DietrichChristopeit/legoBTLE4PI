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

#
   MIT License
  
   Copyright (c) 2021 Dietrich Christopeit
  
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
  
   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.
  
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
  

#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
from multiprocessing import Event
from multiprocessing import Process, Queue
from random import uniform
from time import sleep

"""
First steps...
"""


class Motor:

    def __init__(self, name: str = '', port: int = 0x00, termination: Event = None, execQ: Queue = None):
        self._name: str = name
        self._port: int = port
        self._termination: Event = termination
        self._senderDown: Event = Event()
        self._receiverDown: Event = Event()
        self._motorDown: Event = Event()
        self._execQ: Queue = execQ
        self._Receiver: Process = Process(name="MOTOR RECEIVER", target=self.receiver,
                                          args=(self._execQ, self._termination, self._receiverDown), daemon=False)
        self._Sender: Process = Process(name="MOTOR CMD SENDER", target=self.sender,
                                        args=(self._execQ, self._termination, self._senderDown), daemon=False)

    def motorUp(self):
        self._Sender.start()
        self._Receiver.start()

    def motorDown(self) -> Event:
        self._Receiver.join()
        self._Sender.join()
        self._motorDown.set()
        return self._motorDown

    def receiver(self, execQ: Queue, termination: Event, receiverDown: Event):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        execQ = execQ
        while not termination.is_set():
            if not (execQ.qsize() == 0):
                print("[{}]-[RCV]: RECEIVED item: {}".format(Process.name, execQ.get()))
                sleep(0.5)
                continue

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        receiverDown.set()

    def sender(self, execQ: Queue, termination: Event, senderDown: Event):
        print("[{}]-[MSG]: STARTED...".format(Process.name))
        execQ = execQ
        while not termination.is_set():
            if not (execQ.qsize() == 0):
                print("[{}]-[SND]: SENDING ITEM: {}".format(Process.name, execQ.put(uniform(1, 100))))
                sleep(0.5)
                continue

        print("[{}]-[MSG]: SHUTTING DOWN...".format(Process.name))
        senderDown.set()


if __name__ == '__main__':
    execQ: Queue = Queue()
    termination: Event = Event()

    motor: Motor = Motor(name="TestMotor", port=0x01, termination=termination, execQ=execQ)
    motor.motorUp()
    print("SLEEPING 5")
    termination.set()
    x = motor.motorDown()
    x.wait()
