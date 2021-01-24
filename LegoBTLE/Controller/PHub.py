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
from threading import Thread
from time import sleep

from bluepy import btle

from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.PMotor import Motor, SingleMotor, SynchronizedMotor
from LegoBTLE.MessageHandling.PNotification import PublishingDelegate


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None,
                 terminate: Event = None, debug: bool = False):
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._terminate: Event = Event()
        self._debug = debug
        self._dev: btle.Peripheral = None
        self._officialName: str = None

        self._motors: [Motor] = []

        self._DBTLEQ: Queue = Queue(300)
        self._DBTLENotification = PublishingDelegate(name="BTLE RESULTS DELEGATE", cmdRsltQ=self._DBTLEQ)

        self._E_rsltrcv_STARTED: Event = Event()
        self._E_rsltrcv_STOPPED: Event = Event()
        self._P_rsltrcv_Receiver: Thread = Thread(name="HUB COMMAND RESULTS RECEIVER", target=self.RsltReceiver,
                                                  args=("PRsltReceiver",), daemon=True)

        self._E_cmdexec_STARTED: Event = Event()
        self._E_cmdexec_STOPPED: Event = Event()
        self._P_cmd_EXEC: Process = Process(name="HUB COMMAND EXECUTION", target=self.CmdExec,
                                            args=("PCmdExec",), daemon=True)

    @property
    def P_rsltrcv_Receiver(self) -> Thread:
        return self._P_rsltrcv_Receiver

    @property
    def P_cmd_EXEC(self) -> Process:
        return self._P_cmd_EXEC

    @property
    def E_rsltrcv_STARTED(self) -> Event:
        return self._E_rsltrcv_STARTED

    @property
    def E_cmdexec_STARTED(self) -> Event:
        return self._E_cmdexec_STARTED

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    def register(self, motor: Motor):
        if self._debug:
            print("[HUB]-[MSG]: REGISTERING {} / PORT: {:02x}".format(motor.name, motor.port))
        self._motors.append(motor)

    def startHub(self) -> Event:
        E_starthub: Event = Event()
        E_starthub.clear()
        self._terminate.clear()
        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._name))

        print("[{}]-[MSG]: CONNECTING TO {}...".format(self._name, self._address))
        self._dev = btle.Peripheral(self._address)
        self._dev.withDelegate(self._DBTLENotification)
        print("[{}]-[MSG]: CONNECTION TO {} ESTABLISHED...".format(self._name, self._address))
        if self._debug:
            print("[{}]-[MSG]: SETTING OFFICIAL NAME...".format(self._name))
        self._officialName = self._dev.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name
        self._dev.writeCharacteristic(0x0f, b'\x01\x00')
        self._dev.writeCharacteristic(0x0e, b'\x08\x00\x81\x32\x11\x51\x00\x05')
        if self._debug:
            print("[{}]-[MSG]: OFFICIAL NAME {} SET...".format(self._name, self._officialName))

        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._P_cmd_EXEC.name))
        self._P_cmd_EXEC.start()
        self._E_cmdexec_STARTED.wait()
        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._P_cmd_EXEC.name))

        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._P_rsltrcv_Receiver.name))
        self._P_rsltrcv_Receiver.start()
        self._E_rsltrcv_STARTED.wait()
        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._P_rsltrcv_Receiver.name))
        E_starthub.set()
        E_starthub.wait()

        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._name))
        return E_starthub

    def stopHub(self) -> Event:
        E_stophub: Event = Event()
        E_stophub.clear()
        self._terminate.set()
        self._terminate.wait()
        if self._debug:
            print("[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._name))
        if self._debug:
            print("[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._P_rsltrcv_Receiver.name))
        self._E_rsltrcv_STOPPED.wait()
        self._P_rsltrcv_Receiver.join()
        if self._debug:
            print("[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._P_rsltrcv_Receiver.name))
        if self._debug:
            print("[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._P_cmd_EXEC.name))
        self._E_cmdexec_STOPPED.wait()
        self._P_cmd_EXEC.join()
        if self._debug:
            print("[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._P_cmd_EXEC.name))
        E_stophub.set()
        E_stophub.wait()
        if self._debug:
            print("[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._name))
        return E_stophub

    def CmdExec(self, name: str):
        """This Process reads from a multiprocessing.Queue of commands issued by the Devices.
        Once a data item has been retrieved, it is executed using btle.Peripheral.writeCharacteristic on handle 0x0e
        (fixed for the Lego Technic Hubs).

        :param name:
            A friendly name for the result receiver process.
        :return:
            None
        """
        self._E_cmdexec_STARTED.set()
        print("[{}]-[SIG]: START COMPLETE...".format(name))
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break

            if not self._cmdQ.qsize() == 0:
                command: Command = self._cmdQ.get()
                if self._debug:
                    print(
                            "[{}]-[RCV] <-- [{}]: COMMAND RECEIVED {}".format(name, self._officialName, command.data.hex()))
                self._dev.writeCharacteristic(0x0e, command.data, command.withFeedback)
                if self._debug:
                    print(
                            "[{}]-[SND] --> [{}] = [{}]: Command sent...".format(name, "PRsltReceiver", command.data.hex()))
            # sleep(.001)
        print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(name))
        self._E_cmdexec_STARTED.clear()
        self._E_cmdexec_STOPPED.set()
        return

    def RsltReceiver(self, name: str):
        """The notifier function reads the returned values that come in once a command has been executed on the Hub.
        These values are returned while the respective device (e.g. a Motor) is in action (e.g. turning).
        The return values are put into a multiprocessing.Queue - the _DBTLEQ - by the btle.Peripheral-Delegate Process
        and are distributed to that registered device object (here Motor) whose port equals the port encoded in the
        received result.

        :param name:
            A friendly name for the result receiver process.
        :return:
            None
        """
        self._E_rsltrcv_STARTED.set()
        print("[{}]-[SIG]: START COMPLETE...".format(name))

        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            if self.dev.waitForNotifications(.01):
                if not self._DBTLEQ.qsize() == 0:
                    data: bytes = self._DBTLEQ.get()
                    btleNotification: Command = Command(data=data, port=data[3])
                    if self._debug:
                        print(
                                "[{}]-[RCV] <-- [{}] = [{}]: RESULT FOR PORT {:02}...".format(
                                        name,
                                        self._DBTLENotification.name,
                                        btleNotification.data.hex(),
                                        btleNotification.data[3]))

                    #  send the result of a data sent by delegation to the respective Motor
                    #  to update, e.g. the current degrees and past degrees.
                    for m in self._motors:
                        if isinstance(m, SingleMotor) and (m.port == btleNotification.port):
                            m.Q_rsltrcv_RCV.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}] = [{}]: RESULT SENT TO MOTOR AT PORT {:02}...".format(
                                                name,
                                                m.name,
                                                btleNotification.data,
                                                m.port))
                        if isinstance(m, SynchronizedMotor) and ((m.port==btleNotification.port) or (
                                (m.firstMotor.port==btleNotification.data[len(btleNotification.data) - 1]) and (
                                m.secondMotor.port==btleNotification.data[len(btleNotification.data) - 2]))):
                            m.Q_rsltrcv_RCV.put(btleNotification)
                            if self._debug:
                                print(
                                        "[{}]-[SND] --> [{}]: RESULT SENT TO MOTOR AT PORT {:02}...".format(
                                                name,
                                                m.name,
                                                m.port))
            # sleep(.2)
        print("[{}]-[SIG]: SHUT DOWN COMPLETE...".format(name))
        self._E_rsltrcv_STARTED.clear()
        self._E_rsltrcv_STOPPED.set()
        return
