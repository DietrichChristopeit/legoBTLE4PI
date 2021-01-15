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
from bluepy import btle

from Geraet.Motor import Motor


class Hub(threading.Thread, btle.Peripheral):

    def __init__(self, name: str, adresse: str, execQ: queue.Queue, terminateOn: threading.Event, execQEmpty: threading.Event, debug: bool = False):
        super(Hub, self).__init__()
        self._name: str = name
        self._adresse: str = adresse
        self._execQ: queue.Queue = execQ
        self._motors: [Motor] = []

        self._terminate: threading.Event = terminateOn

        self._delegateQ: queue.Queue = queue.Queue()
        self._delegateRES_Q: queue.Queue = queue.Queue()
        self._Delegate: threading.Thread = None

        self._notifierQ: queue.Queue = queue.Queue()
        self._Notifier: threading.Thread = None

        self._execQEmpty = execQEmpty

        self.setDaemon(True)
        self._debug = debug

    def run(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        self._Delegate = threading.Thread(target=self.delegation, args=(self._terminate,), name="Delegate", daemon=True)
        self._Delegate.start()
        self._Notifier = threading.Thread(target=self.notifier, args=(self._terminate,), name="Notifier", daemon=True)
        self._Notifier.start()

        self.execute()

        self._terminate.wait()

        print("[{}]-[SIG]: SHUTTING DOWN...".format(threading.current_thread().getName()))

        self._Delegate.join()
        self._Notifier.join()

        print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def terminate(self):
        self._terminate.set()
        return

    def register(self, motor: Motor):
        self._motors.append(motor)
        if self._debug:
            print("[{}]-[MSG]: REGISTERED {} ...".format(threading.current_thread().getName(), motor.name))
        return

    def execute(self):
        print("[{}]-[MSG]: Execution loop STARTED...".format(threading.current_thread().getName()))
        while not self._terminate.is_set():
            if not self._execQ.empty():
                self._execQEmpty.clear()
                command = self._execQ.get()
                self._delegateQ.put(command)
                continue
            self._execQEmpty.set()

        print("[{}]-[MSG]: SHUTDOWN COMPLETE EXEC LOOP ...".format(threading.current_thread().getName()))
        return

    def notifier(self, terminate: threading.Event):
        print("[HUB {}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._notifierQ.get()
            if self._debug:
                print("[HUB {}]-[RCV] = [{}]: Command received...".format(threading.current_thread().getName(), command[0]))

            for m in self._motors:
                if m.anschluss == command[1]:
                    if not m.anschluss == 0x01:
                        sleep(round(uniform(0, 5), 2))
                    m.rcvQ.put((command[1], 0x0a))
                    if self._debug:
                        print("[HUB {}]-[SND] -> [{}]: Notification sent...".format(threading.current_thread().getName(),
                                                                                m.name))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def delegation(self, terminate: threading.Event):
        print("[HUB {}]-[MSG]: STARTED...".format(threading.current_thread().getName()))
        while not terminate.is_set():
            command = self._delegateQ.get()
            self._notifierQ.put(command)
            if self._debug:
                print("[HUB {}]-[SND] -> [{}] = [{}]: Command sent...".format(threading.current_thread().getName(), self._Notifier.name, command[0]))

        print("[HUB {}]-[SIG]: SHUT DOWN COMPLETE...".format(threading.current_thread().getName()))
        return