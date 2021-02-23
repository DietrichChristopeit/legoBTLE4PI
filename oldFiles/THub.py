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
import queue
import threading
from time import sleep

from bluepy import btle

import oldFiles.TMotor
from LegoBTLE.Device.old.messaging import Message
from oldFiles.TNotification import PublishingDelegate


class Hub(threading.Thread):
    """This class models the Lego Model's Hub (e.g. Technic Hub 2.0).
    It handles the message flow of payload sent an received. Therefore it creates various (daemonic) threads:
    * Hub: itself runs as a daemonic Thread and spawns:
        * Delegate Thread (daemonic): to receive messages for execution from Devices (e.g. Motor)
        * Notifier Thread (daemonic): to deliver payload results to Devices (e.g. Motors current angle of turn)

    The reason for daemonic threading is, that when the Terminate-Event is sent, the MAIN-Thread acknowledges
    the termination (and subsequent join of the terminated threads) and terminates itself.
    """

    def __init__(self, address='90:84:2B:5E:CF:1F', hubExecQ: queue.Queue = None, terminate: threading.Event = None,
                 debug: bool = False):
        threading.Thread.__init__(self)
        # super(Hub, self).__init__(address)
        self.setDaemon(True)
        print("[HUB]-[CON]: CONNECTING to {}...".format(address))
        self._dev = btle.Peripheral(address)
        print("[HUB]-[CON]: CONNECTED to {}...".format(address))
        self._name: str = self._dev.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name
        # self._name: str = self.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name

        self._address: str = address
        self._execQ: queue.Queue = hubExecQ
        self._execQEmpty: threading.Event = threading.Event()

        self._motors: [oldFiles.TMotor.Motor] = []

        self._HubTerminate: threading.Event = terminate
        self._HubStopped: threading.Event = threading.Event()
        self._HubStarted: threading.Event = threading.Event()
        self._HubExecLoopStarted: threading.Event = threading.Event()
        self._HubExecLoopStopped: threading.Event = threading.Event()

        self._HubDelegateStarted: threading.Event = threading.Event()
        self._HubDelegateStopped: threading.Event = threading.Event()
        self._HubDelegateQ: queue.Queue = queue.Queue()
        self._HubDelegateResponseQ: queue.Queue = queue.Queue()

        self._HubNotifierStarted: threading.Event = threading.Event()
        self._HubNotifierStopped: threading.Event = threading.Event()

        self._BTLEDelegateQ: queue.Queue = queue.Queue()

        print("[{}]-[MSG]: BTLE DELEGATE STARTING...".format(threading.current_thread().getName()))
        self._BTLEDelegate = PublishingDelegate(name="BTLE INTERNAL DELEGATE", cmdRsltQ=self._BTLEDelegateQ)

        self._BTLE2HubDelegate: threading.Thread = threading.Thread(name="BTLE TO HUB DELEGATE", target=self.delegateLegoHub,
                                                                    daemon=True)

        self._HubNotifier: threading.Thread = threading.Thread(target=self.notifierLegoHub,
                                                               name="HUB FROM BTLE DELEGATE",
                                                               daemon=True)

        self._debug = debug

    def run(self):

        print(
            "[{}]-[MSG]: COMMENCE {} START...".format(threading.current_thread().getName(), threading.current_thread().getName()))
        print("CURRENTLY RUNNING THREADS: {}".format(threading.enumerate()))

        print(
            "[{}]-[MSG]: COMMENCE {} START...".format(threading.current_thread().getName(), threading.current_thread().getName()))
        self._dev.withDelegate(self._BTLEDelegate)
        # self.withDelegate(self._BTLEDelegate)
        self._BTLEDelegate.Started.wait()
        print("[{}]-[MSG]: {} COMPLETE...".format(threading.current_thread().getName(), threading.current_thread().getName()))

        self._BTLE2HubDelegate.start()
        print(
            "[{}]-[MSG]: COMMENCE {} START...".format(threading.current_thread().getName(), threading.current_thread().getName()))
        self._HubDelegateStarted.wait()
        print(
            "[{}]-[MSG]: {}START COMPLETE...".format(threading.current_thread().getName(), threading.current_thread().getName()))

        self._HubNotifier.start()
        print(
            "[{}]-[MSG]: COMMENCE {} START...".format(threading.current_thread().getName(), threading.current_thread().getName()))
        self._HubNotifierStarted.wait()
        print(
            "[{}]-[MSG]: {} START COMPLETE...".format(threading.current_thread().getName(), threading.current_thread().getName()))

        print(
            "[{}]-[MSG]: {} START COMPLETE...".format(threading.current_thread().getName(), threading.current_thread().getName()))
        self._HubExecLoopStopped.clear()
        print("CURRENTLY RUNNING THREADS: {}".format(threading.enumerate()))

        self._dev.writeCharacteristic(0x0f, b'\x01\x00')  # subscribe to general HUB Notifications
        # self.writeCharacteristic(0x0f, b'\x01\x00')  # subscribe to general HUB Notifications
        print("[{}]:[EXECUTION_LOOP]-[MSG]: COMMENCE START...".format(threading.current_thread().getName()))
        self._HubStarted.set()
        self.runExecutionLoop()

        self._HubTerminate.wait()
        print("[{}]-[SIG_RCV]: SHUTDOWN SIGNAL RECEIVED...".format(threading.current_thread().getName()))

        print("[{}]-[SIG_SND]: COMMENCE DELEGATE SHUTDOWN...".format(threading.current_thread().getName()))
        self._HubDelegateStopped.wait()
        self._BTLE2HubDelegate.join()
        print("[{}]-[SIG_RCV]: DELEGATE SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))

        print("[{}]-[SIG_SND]: COMMENCE NOTIFIER SHUTDOWN...".format(threading.current_thread().getName()))
        self._HubNotifierStopped.wait()
        self._HubNotifier.join()
        print("[{}]-[SIG_RCV]: NOTIFIER SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))

        print("[{}]-[SIG_SND]: COMMENCE EXEC LOOP SHUTDOWN...".format(threading.current_thread().getName()))
        self._HubExecLoopStopped.wait()
        print("[{}]-[SIG_RCV]: EXEC LOOP SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        print(
                "[{}]-[SIG_RCV]: COMMAND HANDLING SYSTEM SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        print(
                "[{}]-[SIG_RCV]: COMMENCE BTLE NOTIFIER SHUTDOWN...".format(threading.current_thread().getName()))

        self._dev.disconnect()
        # self.disconnect()
        self._HubStarted.clear()
        self._HubStopped.set()
        print("[{}]-[SIG_SND]: SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def register(self, motor: oldFiles.TMotor.Motor):
        """This function connects a Device (e.g. a Motor) with the Hub.
        This is comparable to connecting the cable between the Device and
        the Hub. Thus, access to the Device's attributes is possible.

        :param motor:
            The new Device that will be registered with the hub.
        :return:
            None
        """
        self._dev.writeCharacteristic(0x0e, bytes.fromhex('0a0041{:02}020100000001'.format(motor.port)), True)
        # self.writeCharacteristic(0x0e, bytes.fromhex('0a0041{:02}020100000001'.format(motor.port)), True)
        self._motors.append(motor)
        if self._debug:
            print("[{}]:[REGISTER]-[MSG]: REGISTERED {} ...".format(threading.current_thread().getName(), motor.name))
        return

    def runExecutionLoop(self):
        """The ExecutionLoop is called by the Hub's run(self) Method.
            It could easily put into the run(self) Method.
            Clearly the level of encapsulation looks a bit awkward - for educational purposes
            , i.e., trying to show only short code fragments at a time, it was thought to be the right approach.

            The Method tries to get a payload sent (through _execQ) from a Motor Thread and put it into the Delegate
            Thread's Queue (_execQ) for writing it to the Hub via btle.Peripheral.writeCharacteristic(0x0e, ...)

            If the Device's send Queue (_execQ) is:
                 * NOT empty:
                        * unset the Event that it is empty, if it was so set before
                        * get the next payload from _execQ
                        * put it in the Delegate Thread's Queue (_HubDelegateQ) for execution
                 * empty: flag the empty state by setting the _execQEmpty-Event to True
        :return:
            None
        """
        self._HubExecLoopStarted.set()
        print("[{}]:[EXECUTION_LOOP]-[MSG]: START COMPLETE...".format(threading.current_thread().getName()))
        while not self._HubTerminate.is_set():
            if not self._execQ.empty():
                self._execQEmpty.clear()
                command: Message = self._execQ.get()
                if self._debug:
                    print(
                            "[{}]:[EXECUTION_LOOP]-[MSG]: COMMAND RECEIVED {} FROM DEVICE_INIT {:02}...".format(
                                threading.current_thread().getName(),
                                command.payload.hex(), command.port))
                self._HubDelegateQ.put(command)
                continue
            self._execQEmpty.set()

        self._HubExecLoopStarted.clear()
        self._HubExecLoopStopped.set()
        print("[HUB]:[EXECUTION_LOOP]-[MSG]: SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    def notifierLegoHub(self):
        """The notifier function reads the returned values that come in once a payload has been executed on the hub.
            These values are returned while the respective device (e.g. a Motor) is in action (e.g. turning).
            The return values are put into a queue - the _BTLEDelegateQ - by the btle.Peripheral-Delegate object and
            are distributed to the respective Motor Thread here.

        :return:
            None
        """
        self._HubNotifierStarted.set()
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))

        while not self._HubTerminate.is_set():
            if self._dev.waitForNotifications(1.5):
                # if self.waitForNotifications(1.5):
                try:
                    data: bytes = self._BTLEDelegateQ.get()
                    btleNotification: Message = Message(payload=data)
                    if self._debug:
                        print(
                                "[{}]-[RCV] <-- [{}] = [{}]: UpStreamMessageBuilder received PORT {:02}...".format(
                                        threading.current_thread().getName(),
                                        self._BTLEDelegate.name,
                                        btleNotification.payload.hex(),
                                        btleNotification.payload[3]))

                    #  send the result of a payload sent by delegation to the respective Motor
                    #  to update, e.g. the current degrees and past degrees.
                    for m in self._motors:
                        if isinstance(m, oldFiles.TMotor.SingleMotor) and (m.port==btleNotification.port):
                            m.rcvQ.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}]: Notification sent...".format(
                                                threading.current_thread().getName(),
                                                m.name))
                        if isinstance(m, oldFiles.TMotor.SynchronizedMotor) and ((m.port==btleNotification.port) or (
                                (m.firstMotor.port == btleNotification.payload[len(btleNotification.payload) - 1]) and (
                                m.secondMotor.port == btleNotification.payload[len(btleNotification.payload) - 2]))):
                            m.rcvQ.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}]: Notification sent...".format(
                                                threading.current_thread().getName(),
                                                m.name))
                except queue.Empty:
                    sleep(0.5)
                    continue

        self._HubNotifierStarted.clear()
        self._HubNotifierStopped.set()
        print("[{}]-[SIG]: SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        return

    @property
    def HubStopped(self) -> threading.Event:
        return self._HubStopped

    @property
    def HubStarted(self) -> threading.Event:
        return self._HubStarted

    @property
    def execQ(self) -> queue.Queue:
        return self._execQ

    @property
    def hubTerminating(self) -> threading.Event:
        return self._HubTerminate

    def terminate(self):
        self._HubTerminate.set()
        return

    def delegateLegoHub(self):
        """The delegate function is a Daemonic Thread that reads a queue.Queue of messages issued by the Devices.
            Once a payload item is read it is executed with btle.Peripheral.writeCharacteristic on
            handle 0x0e (fixed for the Lego Technic Hubs).

       :return:
            None
        """

        self._HubDelegateStarted.set()
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().getName()))

        while not self._HubTerminate.is_set():
            if not self._HubDelegateQ.empty():
                # payload[0]: contains the hex bytes comprising the payload,
                # payload[1]: True or False for "with return messages" oder "without return messages"

                command: Message = self._HubDelegateQ.get()
                print("[{}]-[MSG]: COMMAND RECEIVED {}".format(threading.current_thread().getName(),
                                                               command.payload.hex()))
                self._dev.writeCharacteristic(0x0e, command.payload, command.withFeedback)
                # self.writeCharacteristic(0x0e, command.payload, command.withFeedback)
                if self._debug:
                    print("[{}]-[SND] --> [{}] = [{}]: UpStreamMessageBuilder sent...".format(
                            threading.current_thread().getName(),
                            self._HubNotifier.name, command.payload.hex()))

                continue
            sleep(0.05)
            continue

        self._HubDelegateStarted.clear()
        self._HubDelegateStopped.set()
        print("[{}]-[SIG]: SHUTDOWN COMPLETE...".format(threading.current_thread().getName()))
        return
