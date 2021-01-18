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

from LegoBTLE.SystemStartupHandling import SubsystemConfig
from queue import Queue
from threading import Thread, Event, current_thread, Condition, enumerate
from time import sleep

from bluepy import btle
from deprecated.sphinx import deprecated

from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.Motor import SingleMotor, SynchronizedMotor, Motor
from LegoBTLE.MessageHandling.Notification import PublishingDelegate


class Hub(btle.Peripheral, Thread):
    """This class models the Lego Model's Hub (e.g. Technic Hub 2.0).
    It handles the message flow of data sent an received. Therefore it creates various (daemonic) threads:
    * Hub: itself runs as a daemonic Thread and spawns:
        * Delegate Thread (daemonic): to receive commands for execution from Devices (e.g. Motor)
        * Notifier Thread (daemonic): to deliver data results to Devices (e.g. Motors current angle of turn)

    The reason for daemonic threading is, that when the Terminate-Event is sent, the MAIN-Thread acknowledges
    the termination (and subsequent join of the terminated threads) and terminates itself.
    """

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', debug: bool = False):
        Thread.__init__(self)
        self.setDaemon(True)
        print("[HUB]-[CON]: CONNECTING to {}...".format(address))
        super().__init__(address)
        print("[HUB]-[CON]: CONNECTED to {}...".format(address))
        self._name: str = self.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name
        self._address: str = address
        self._execQ: Queue = SubsystemConfig.hubExecQ
        self._motors: [Motor] = []

        self._delegateStarted: Event = Event()
        self._DelegateCondition: Condition = Condition()

        self._notifierStarted: Event = Event()
        self._NotifierCondition: Condition = Condition()

        self._terminate: Event = SubsystemConfig.terminateEvent

        self._delegateQ: Queue = Queue()
        self._delegateRES_Q: Queue = Queue()
        # self._Delegate: threading.Thread = None

        self._notifierQ: Queue = Queue()
        # self._Notifier: threading.Thread = None
        print("[{}]-[MSG]: NOTIFIER STARTING...".format(current_thread().getName()))
        self._NotifierDelegate = PublishingDelegate(name="PUBLISHING DELEGATE", cmdRsltQ=self._notifierQ)
        self.withDelegate(self._NotifierDelegate)
        print("[{}]-[MSG]: NOTIFIER STARTED...".format(current_thread().getName()))
        self._Delegate: Thread = Thread(target=self.delegateLegoHub, args=(self._terminate,), name="Delegate",
                                        daemon=True)

        self._Notifier: Thread = Thread(target=self.notifierLegoHub, args=(self._terminate,), name="Notifier",
                                        daemon=True)
        self._execQEmpty: Event = SubsystemConfig.hubExecQEmptyEvent

        self._debug = debug

    def run(self):

        print("[{}]-[MSG]: STARTED...".format(current_thread().getName()))
        self._Delegate.start()
        print("THREADS: {}".format(enumerate()))
        print("[{}]-[MSG]: WAITING FOR DELEGATE TO START...".format(current_thread().getName()))
        self._delegateStarted.wait()
        print("[{}]-[MSG]: DELEGATE STARTED...".format(current_thread().getName()))

        self._Notifier.start()
        print("[{}]-[MSG]: WAITING FOR NOTIFIER TO START...".format(current_thread().getName()))
        self._notifierStarted.wait()
        print("[{}]-[MSG]: NOTIFIER STARTED...".format(current_thread().getName()))

        self.writeCharacteristic(0x0f, b'\x01\x00')  # subscribe to general HUB Notifications
        print("[{}]-[MSG]: STARTING EXEC LOOP...".format(current_thread().getName()))
        self.runExecutionLoop()
        print("[{}]-[MSG]: STARTED EXEC LOOP...".format(current_thread().getName()))

        with SubsystemConfig.terminateCondition, self._DelegateCondition, self._NotifierCondition:
            SubsystemConfig.terminateCondition.wait_for(lambda: self._terminate.is_set())
            print("[{}]-[SIG]: SHUTTING DOWN HUB THREADS...".format(current_thread().getName()))
            SubsystemConfig.terminateCondition.notifyAll()
            self._DelegateCondition.wait_for(lambda: not self._delegateStarted.is_set())
            self._Delegate.join()
            print("[{}]-[SIG]: DELEGATE SHUT DOWN COMPLETE...".format(current_thread().getName()))
            self._NotifierCondition.wait_for(lambda: not self._notifierStarted.is_set())
            print("[{}]-[SIG]: NOTIFIER SHUT DOWN COMPLETE...".format(current_thread().getName()))
            self._Notifier.join()
            print("[{}]-[MSG]: STOPPED EXEC LOOP...".format(current_thread().getName()))
            print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(current_thread().getName()))
            SubsystemConfig.terminateCondition.notifyAll()
            return

    @deprecated(reason="Done by setting Event in MAIN Thread.", version='1.1', action="Keep for now")
    def terminate(self):
        self._terminate.set()
        return

    def register(self, motor: Motor):
        """This function connects a Device (e.g. a Motor) with the Hub.
        This is comparable to connecting the cable between the Device and
        the Hub. Thus, access to the Device's attributes is possible.

        :param motor:
            The new Device that will be registered with the hub.
        :return:
            None
        """
        self.writeCharacteristic(0x0e, bytes.fromhex('0a0041{:02}020100000001'.format(motor.port)), True)
        self._motors.append(motor)
        if self._debug:
            print("[{}]-[MSG]: REGISTERED {} ...".format(current_thread().getName(), motor.name))
        return

    def runExecutionLoop(self):
        """The ExecutionLoop is called by the Hub's run(self) Method.
            It could easily put into the run(self) Method.
            Clearly the level of encapsulation looks a bit awkward - for educational purposes
            , i.e., trying to show only short code fragments at a time, it was thought to be the right approach.

            The Method tries to get a data sent (through _execQ) from a Motor Thread and put it into the Delegate
            Thread's Queue (_execQ) for writing it to the Hub via btle.Peripheral.writeCharacteristic(0x0e, ...)

            If the Device's send Queue (_execQ) is:
                 * NOT empty:
                        * unset the Event that it is empty, if it was so set before
                        * get the next data from _execQ
                        * put it in the Delegate Thread's Queue (_delegateQ) for execution
                 * empty: flag the empty state by setting the _execQEmpty-Event to True
        :return:
            None
        """
        print("[{} / EXECUTE LOOP]-[MSG]: STARTED...".format(current_thread().getName()))
        while not self._terminate.is_set():
            if not self._execQ.empty():
                self._execQEmpty.clear()
                command: Command = self._execQ.get()
                if self._debug:
                    print(
                        "[{} / EXECUTE LOOP]-[MSG]: COMMAND RECEIVED {}...".format(current_thread().getName(),
                                                                                   command.data.hex()))
                self._delegateQ.put(command)
                continue
            self._execQEmpty.set()

        print("[HUB {} / EXECUTE LOOP]-[MSG]: SHUTDOWN COMPLETE...".format(current_thread().getName()))
        return

    def notifierLegoHub(self, terminate: Event):
        """The notifier function reads the returned values that come in once a data has been executed on the hub.
            These values are returned while the respective device (e.g. a Motor) is in action (e.g. turning).
            The return values are put into a queue - the _notifierQ - by the btle.Peripheral-Delegate object and
            are distributed to the respective Motor Thread here.

        :param terminate:
            The event that tells the Notifier Thread to shut down, thus ending the Notifier Thread.
        :return:
            None
        """
        self._notifierStarted.set()
        print("[HUB {} / NOTIFIER]-[MSG]: STARTED...".format(current_thread().getName()))
        print("THREADS: {}".format(enumerate()))
        while not terminate.is_set():
            if self.waitForNotifications(1.5):
                try:
                    data: bytes = self._notifierQ.get()
                    notification: Command = Command(data=data, port=data[3])
                    if self._debug:
                        print(
                            "[HUB {} / NOTIFIER]-[RCV] = [{}]: Command received PORT {:02}...".format(
                                current_thread(

                                ).getName(),
                                notification.data.hex(),
                                notification.data[3]))
                    #  send the result of a data sent by delegation to the respective Motor
                    #  to update, e.g. the current degrees and past degrees.
                    for m in self._motors:
                        if isinstance(m, SingleMotor) and (m.port == notification.port):
                            m.rcvQ.put(notification)
                            if self._debug:
                                print(
                                    "[HUB {} / NOTIFIER]-[SND] --> [{}]: Notification sent...".format(
                                        current_thread().getName(),
                                        m.name))
                        if isinstance(m, SynchronizedMotor) and ((m.port == notification.port) or (
                                (m.firstMotor.port == notification.data[len(notification.data) - 1]) and (
                                m.secondMotor.port == notification.data[len(notification.data) - 2]))):
                            m.rcvQ.put(notification)
                            if self._debug:
                                print(
                                    "[HUB {} / NOTIFIER]-[SND] --> [{}]: Notification sent...".format(
                                        current_thread().getName(),
                                        m.name))
                except queue.Empty:
                    sleep(0.5)
                    continue

        with self._NotifierCondition:
            self._notifierStarted.clear()
            print("[HUB {} / NOTIFIER]-[SIG]: SHUT DOWN COMPLETE...".format(current_thread().getName()))
            self._NotifierCondition.notifyAll()
            return

    def delegateLegoHub(self, terminate: Event):
        """The delegate function is a Daemonic Thread that reads a queue.Queue of commands issued by the Devices.
            Once a data is read it is executed with btle.Peripheral.writeCharacteristic on
            handle 0x0e (fixed for the Lego Technic Hubs).

        :param terminate:
            The event that tells the Delegate Thread to shut down, thus ending the Delegate Thread.
        :return:
            None
        """
        self._delegateStarted.set()
        print("[HUB {} / DELEGATE]-[MSG]: STARTED...".format(current_thread().getName()))
        print("THREADS: {}".format(enumerate()))
        while not terminate.is_set():
            if not self._delegateQ.empty():
                # data[0]: contains the hex bytes comprising the data,
                # data[1]: True or False for "with return messages" oder "without return messages"

                command: Command = self._delegateQ.get()
                print("[HUB {} / DELEGATE]-[MSG]: COMMAND RECEIVED {}".format(current_thread().getName(),
                                                                              command.data.hex()))
                self.writeCharacteristic(0x0e, command.data, command.withFeedback)
                if self._debug:
                    print("[HUB {} / DELEGATE]-[SND] --> [{}] = [{}]: Command sent...".format(
                        current_thread().getName(),
                        self._Notifier.name, command.data.hex()))

                continue

        with self._DelegateCondition:
            self._delegateStarted.clear()
            print("[HUB {} / DELEGATE]-[SIG]: SHUT DOWN COMPLETE...".format(current_thread().getName()))
            self._DelegateCondition.notifyAll()
            return
