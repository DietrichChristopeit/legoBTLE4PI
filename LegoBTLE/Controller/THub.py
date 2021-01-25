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
from queue import Empty, Queue
from threading import Thread, Event
from time import sleep

from bluepy import btle
from colorama import Fore, Style

from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.TMotor import Motor, SingleMotor, SynchronizedMotor
from LegoBTLE.MessageHandling.TNotification import PublishingDelegate


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None,
                 terminate: Event = None, debug: bool = False):
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._Q_result: Queue = Queue(maxsize=500)

        self._E_TERMINATE: Event = terminate
        self._E_HUB_TERMINATED: Event = Event()
        self._E_HUB_STARTED: Event = Event()
        self._E_PROCESSES_TERMINATE: Event = Event()

        self._debug = debug
        self._dev: btle.Peripheral = None
        self._officialName: str = None

        self._motors: [Motor] = []

        self._Q_BTLE_DELEGATE: Queue = Queue(500)
        self._BTLE_DelegateNotification = PublishingDelegate(name="BTLE RESULTS DELEGATE", cmdRsltQ=self._Q_BTLE_DELEGATE)

        self._E_rsltrcv_STARTED: Event = Event()
        self._E_rsltrcv_STOPPED: Event = Event()
        self._T_rsltrcv_Receiver: Thread = Thread(name="HUB COMMAND RESULTS RECEIVER", target=self.RsltReceiver,
                                                  args=("PRsltReceiver",), daemon=True)

        self._E_cmdexec_STARTED: Event = Event()
        self._E_cmdexec_STOPPED: Event = Event()
        self._T_cmd_EXEC: Thread = Thread(name="HUB COMMAND EXECUTION", target=self.CmdExec,
                                          args=("PCmdExec",), daemon=True)
        self._T_resultQ_LISTENER: Thread = Thread(name="HUB RESULT QUEUE LISTENER", target=self.resultQ, args=("HUB RESULT "
                                                                                                                 "QUEUE "
                                                                                                                 "LISTENER",),
                                                  daemon=True)
        self._E_resultQ_LISTENER_STARTED: Event = Event()
        self._E_resultQ_LISTENER_STOPPED: Event = Event()

        self._T_hub_STOP: Thread = Thread(name="HUB STOP LISTENER", target=self.stopHub, daemon=True)

    @property
    def T_rsltrcv_Receiver(self) -> Thread:
        return self._T_rsltrcv_Receiver

    @property
    def T_cmd_EXEC(self) -> Thread:
        return self._T_cmd_EXEC

    @property
    def E_rsltrcv_STARTED(self) -> Event:
        return self._E_rsltrcv_STARTED

    @property
    def E_cmdexec_STARTED(self) -> Event:
        return self._E_cmdexec_STARTED

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    @property
    def E_HUB_STARTED(self) -> Event:
        return self._E_HUB_STARTED

    @property
    def E_HUB_TERMINATED(self) -> Event:
        return self._E_HUB_TERMINATED

    def register(self, motor: Motor):
        if self._debug:
            print("[HUB]-[MSG]: REGISTERING {} / PORT: {:02x}".format(motor.name, motor.port))
        self._motors.append(motor)
        self._dev.writeCharacteristic(0x0e, bytes.fromhex("0a0041{:02}020100000001".format(motor.port)), withResponse=True)
        sleep(1)
        return

    def startHub(self):
        self._E_HUB_STARTED.clear()
        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._name))

        print("[{}]-[MSG]: CONNECTING TO {}...".format(self._name, self._address))
        self._dev = btle.Peripheral(self._address)
        self._dev.withDelegate(self._BTLE_DelegateNotification)
        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._T_resultQ_LISTENER.name))
        self._T_resultQ_LISTENER.start()
        self._E_resultQ_LISTENER_STARTED.wait()
        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._T_resultQ_LISTENER.name))
        print("[{}]-[MSG]: CONNECTION TO {} ESTABLISHED...".format(self._name, self._address))
        if self._debug:
            print("[{}]-[MSG]: SETTING OFFICIAL NAME...".format(self._name))
        self._officialName = self._dev.readCharacteristic(0x07).decode("utf-8")  # get the Hub's official name
        self._dev.writeCharacteristic(0x0f, b'\x01\x00')
        self._dev.writeCharacteristic(0x0e, b'\x08\x00\x81\x32\x11\x51\x00\x05')
        if self._debug:
            print("[{}]-[MSG]: OFFICIAL NAME {} SET...".format(self._name, self._officialName))

        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._T_cmd_EXEC.name))
        self._T_cmd_EXEC.start()
        self._E_cmdexec_STARTED.wait()
        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._T_cmd_EXEC.name))

        if self._debug:
            print("[{}]-[MSG]: COMMENCE START {}...".format(self._name, self._T_rsltrcv_Receiver.name))
        self._T_rsltrcv_Receiver.start()
        self._E_rsltrcv_STARTED.wait()
        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._T_rsltrcv_Receiver.name))
        self._E_HUB_STARTED.set()
        self._E_HUB_STARTED.wait()

        if self._debug:
            print("[{}]-[MSG]: {} START COMPLETE...".format(self._name, self._name))
        self._T_hub_STOP.start()
        return

    def stopHub(self):
        self._E_TERMINATE.wait()
        self._E_PROCESSES_TERMINATE.set()
        if self._debug:
            print(Fore.YELLOW + Style.BRIGHT + "[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._name))
        if self._debug:
            print(Fore.YELLOW + Style.BRIGHT + "[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._T_rsltrcv_Receiver.name))
        self._E_rsltrcv_STOPPED.wait()

        if self._debug:
            print(Fore.GREEN + Style.BRIGHT + "[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._T_rsltrcv_Receiver.name))
        if self._debug:
            print(Fore.YELLOW + Style.BRIGHT + "[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._T_cmd_EXEC.name))
        self._E_cmdexec_STOPPED.wait()

        if self._debug:
            print(Fore.GREEN + Style.BRIGHT + "[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._T_cmd_EXEC.name))
        if self._debug:
            print(Fore.YELLOW + Style.BRIGHT + "[{}]-[MSG]: COMMENCE SHUT DOWN {}...".format(self._name, self._T_resultQ_LISTENER.name))
        self._E_resultQ_LISTENER_STOPPED.wait()
        self._T_resultQ_LISTENER.join()
        self._T_cmd_EXEC.join()
        self._T_rsltrcv_Receiver.join()
        if self._debug:
            print(Fore.GREEN + Style.BRIGHT + "[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._T_rsltrcv_Receiver.name))

        self._E_HUB_TERMINATED.set()
        if self._debug:
            print(Fore.GREEN + Style.BRIGHT + "[{}]-[MSG]: {} SHUT DOWN COMPLETE...".format(self._name, self._name))
        return

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
        print(Fore.GREEN + Style.BRIGHT + "[{}]-[SIG]: START COMPLETE...".format(name))
        print(Style.RESET_ALL)
        while not self._E_PROCESSES_TERMINATE.is_set():
            if self._E_PROCESSES_TERMINATE.is_set():
                break

            if not self._cmdQ.qsize() == 0:
                command: Command = self._cmdQ.get()
                if self._debug:
                    print(Fore.MAGENTA + Style.BRIGHT +
                          "[{}]-[RCV] <-- [{}]: COMMAND RECEIVED {}".format(name, self._officialName, command.data.hex()))
                    print(Style.RESET_ALL)
                self._dev.writeCharacteristic(0x0e, command.data, command.withFeedback)
                if self._debug:
                    print(Fore.MAGENTA + Style.BRIGHT +
                          "[{}]-[SND] --> [{}] = [{}]: Command sent...".format(name, "PRsltReceiver", command.data.hex()))
                    print(Style.RESET_ALL)
            sleep(.01)
        print(Fore.GREEN + Style.BRIGHT + "[{}]-[SIG]: SHUT DOWN COMPLETE...".format(name))
        print(Style.RESET_ALL)
        self._E_cmdexec_STARTED.clear()
        self._E_cmdexec_STOPPED.set()
        self._dev.disconnect()
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
        print(Fore.GREEN + Style.BRIGHT + "[{}]-[SIG]: START COMPLETE...".format(name))
        print(Style.RESET_ALL)

        while not self._E_PROCESSES_TERMINATE.is_set():
            if self.dev.waitForNotifications(0.4):
                continue
            # sleep(0.01)
        print(Fore.GREEN + Style.BRIGHT + "[{}]-[SIG]: SHUT DOWN COMPLETE...".format(name))
        print(Style.RESET_ALL)
        self._E_rsltrcv_STARTED.clear()
        self._E_rsltrcv_STOPPED.set()
        return

    def resultQ(self, name: str):
        self._E_resultQ_LISTENER_STARTED.set()
        while not self._E_PROCESSES_TERMINATE.is_set():
            if self._E_PROCESSES_TERMINATE.is_set():
                break
            data: bytes
            try:
                data = self._Q_BTLE_DELEGATE.get(timeout=.4)
            except Empty:
                pass
            else:
                btleNotification: Command = Command(data=data, port=data[3])
                if self._debug:
                    print(Fore.MAGENTA + Style.BRIGHT +
                          "[{}]-[RCV] <-- [{}] = [{}]: RESULT FOR PORT {:02}...".format(
                                  name,
                                  self._BTLE_DelegateNotification.name,
                                  btleNotification.data.hex(),
                                  btleNotification.data[3]))
                    print(Style.RESET_ALL)

                #  send the result of a data sent by delegation to the respective Motor
                #  to update, e.g. the current degrees and past degrees.
                for m in self._motors:
                    if isinstance(m, SingleMotor) and (m.port == btleNotification.port):
                        m.Q_rsltrcv_RCV.put(btleNotification)
                        if self._debug:
                            print(Fore.MAGENTA + Style.BRIGHT +
                                  "[{}]-[SND] --> [{}] = [{}]: RESULT SENT TO MOTOR AT PORT {:02}...".format(
                                          name,
                                          m.name,
                                          btleNotification.data.hex(),
                                          m.port))
                            print(Style.RESET_ALL)
                    if isinstance(m, SynchronizedMotor) and ((m.port == btleNotification.port) or (
                            (m.firstMotor.port == btleNotification.data[len(btleNotification.data) - 1]) and (
                            m.secondMotor.port == btleNotification.data[len(btleNotification.data) - 2]))):
                        m.Q_rsltrcv_RCV.put(btleNotification)
                        if self._debug:
                            print(Fore.MAGENTA + Style.BRIGHT +
                                  "[{}]-[SND] --> [{}]: RESULT SENT TO MOTOR AT PORT {:02}...".format(
                                          name,
                                          m.name,
                                          m.port))
                            print(Style.RESET_ALL)
        print(Fore.GREEN + Style.BRIGHT + "[{}]-[SIG]: SHUT DOWN COMPLETE...".format(name))
        print(Style.RESET_ALL)
        self._E_resultQ_LISTENER_STARTED.clear()
        self._E_resultQ_LISTENER_STOPPED.set()
        return
