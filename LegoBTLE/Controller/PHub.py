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

from LegoBTLE.Device import Motor
from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.PMotor import SingleMotor, SynchronizedMotor
from LegoBTLE.MessageHandling.PNotification import PublishingDelegate


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None, terminate: Event = None, debug: bool = False):
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._terminate: Event = terminate
        self._debug = debug

        self._motors: [Motor] = []
        self._PCmdExecStarted: Event = Event()

        self._dev = btle.Peripheral(self._address)
        self._officialName = self._dev.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name

        self._DBTLEQ: Queue = Queue()
        self._DBTLENotification = PublishingDelegate(name="BTLE RESULTS DELEGATE", cmdRsltQ=self._DBTLEQ)
        self._dev.withDelegate(self._DBTLENotification)

        self._PRsltReceiver: Process = Process(name="HUB FROM BTLE DELEGATE", target=Hub.PRsltReceiver, args=("PRsltReceiver", ), daemon=False)
        self._PRsltReceiverStarted: Event = Event()

    @property
    def PCmdExecStarted(self) -> Event:
        return self._PCmdExecStarted

    def register(self, motor: Motor):
        self._motors.append(motor)

    def PCmdExec(self, name: str):
        print("[{}]-[MSG]: STARTED...".format(self._name))
        self._PCmdExecStarted.set()
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break

            if not self._cmdQ.qsize() == 0:
                command: Command = self._cmdQ.get()
                print("[{}]-[MSG]: COMMAND RECEIVED {}".format(self._officialName, command.data.hex()))
                self._dev.writeCharacteristic(0x0e, command.data, command.withFeedback)
                if self._debug:
                    print("[{}]-[SND] --> [{}] = [{}]: Command sent...".format(name, "notifierLegoHub", command.data.hex()))
# NOCH NICHT GEàNDERT
            for m in self._motors:
                if m.port == p:
                    m.rsltQ.put(e)
                    print("[{}]-[SND]: COMMAND RESULTS SENT {} to PORT {}".format(self._name, e, m.port))
            # sleep(.001)  # to make sending and receiving (port freeing) more evenly distributed

        print("[{}]-[MSG]: SHUTTING DOWN...".format(self._name))
        self._PCmdExecStarted.clear()
        return

    def PRsltReceiver(self, name):
        """The notifier function reads the returned values that come in once a data has been executed on the hub.
            These values are returned while the respective device (e.g. a Motor) is in action (e.g. turning).
            The return values are put into a queue - the _DBTLEQ - by the btle.Peripheral-Delegate object and
            are distributed to the respective Motor Thread here.

        :return:
            None
        """
        self._PRsltReceiverStarted.set()
        print("[{}]-[MSG]: STARTED...".format(name))

        while not self._terminate.is_set():
            if self._dev.waitForNotifications(1.5):
                if not self._DBTLEQ.qsize() == 0:
                    data: bytes = self._DBTLEQ.get()
                    btleNotification: Command = Command(data=data, port=data[3])
                    if self._debug:
                        print(
                                "[{}]-[RCV] <-- [{}] = [{}]: Command received PORT {:02}...".format(
                                        name,
                                        self._DBTLENotification.name,
                                        btleNotification.data.hex(),
                                        btleNotification.data[3]))

                    #  send the result of a data sent by delegation to the respective Motor
                    #  to update, e.g. the current degrees and past degrees.
                    for m in self._motors:
                        if isinstance(m, SingleMotor) and (m.port == btleNotification.port):
                            m.rcvQ.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}]: Notification sent...".format(
                                                name,
                                                m.name))
                        if isinstance(m, SynchronizedMotor) and ((m.port == btleNotification.port) or (
                                (m.firstMotor.port == btleNotification.data[len(btleNotification.data) - 1]) and (
                                m.secondMotor.port == btleNotification.data[len(btleNotification.data) - 2]))):
                            m.rcvQ.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}]: Notification sent...".format(
                                                name,
                                                m.name))
                sleep(.05)
                continue

        self._PRsltReceiverStarted.clear()
        print("[{}]-[SIG]: SHUTDOWN COMPLETE...".format(name))
        return
