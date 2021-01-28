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
from threading import Event, current_thread
from queue import Queue, Empty, Full

from bluepy import btle
from bluepy.btle import BTLEInternalError

from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.TMotor import Motor


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None,
                 terminate: Event = None, debug: bool = False):
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._Q_result: Queue = Queue(maxsize=-1)
        self._E_TERMINATE: Event = terminate

        self._debug = debug
        print("[{}]-[MSG]: TRYING TO CONNECT TO {}".format(self._name, self._address))
        self._dev: btle.Peripheral = btle.Peripheral(address)
        print("[{}]-[MSG]: CONNECTION SUCCESSFUL TO {}".format(self._name, self._address))
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        print("[{}]-[MSG]: OFFICIAL NAME: {}".format(self._name, self._officialName))
        self._registeredMotors: [Motor] = []

        self._Q_CMDRSLT: Queue = Queue(maxsize=-1)
        self._BTLE_DelegateNotifications = self.BTLEDelegate(self._Q_CMDRSLT)
        self._dev.withDelegate(self._BTLE_DelegateNotifications)

        return

    class BTLEDelegate(btle.DefaultDelegate):

        def __init__(self, Q_CMDRSLT: Queue):
            super().__init__()
            self._Q_BCMDRSLT: Queue = Q_CMDRSLT
            return

        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            try:
                m: Command = Command(bytes.fromhex(data.hex()), data[3], True)
                self._Q_BCMDRSLT.put(m)
            except Full:
                print("Collision...")
                pass
            return

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    def listenNotif(self):
        print("[{}]-[SIG]: STARTED...".format(current_thread().getName()))
        while not self._E_TERMINATE.is_set():  # waiting loop for notifications from Hub
            # if self._dev.waitForNotifications(1.0):
            #  continue
            try:
                if self._dev.waitForNotifications(.02):
                    continue
            except BTLEInternalError:
                continue
        print("[{}]-[SIG]: SHUT DOWN...".format(current_thread().getName()))
        return

    def register(self, motor: Motor):
        if self._debug:
            print("[HUB]-[MSG]: REGISTERING {} / PORT: {:02x}".format(motor.name, motor.port))
        self._registeredMotors.append(motor)
        return

    def dispatch(self, cmd: Command):
        couldPut: bool = False

        for m in self._registeredMotors:
            if m.port == cmd.port:
                print("[{}]-[SND] --> [{}]-[{:02}]: RSLT = {}".format(
                        current_thread().getName(), m.name, m.port, cmd.data.hex()))
                m.Q_rsltrcv_RCV.put(cmd)
                couldPut = True
        if not couldPut:
            print("[{}:DISPATCHER]-[MSG]: non-dispatchable Notification {}".format(current_thread().getName(),
                                                                                   cmd.data.hex()))
        return

    def res_rcv(self):
        print("STARTING {}".format(current_thread().getName()))
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                command: Command = self._cmdQ.get_nowait()
            except Empty:
                pass
            else:
                print("[{}]-[RCV] <-- [{:02}]-[SND]: CMD RECEIVED: {}...".format(current_thread().getName(),
                                                                                 command.port, command.data.hex()))
                self._dev.writeCharacteristic(0x0e, command.data, True)

        print("[{}]-[SIG]: SHUT DOWN...".format(current_thread().getName()))
        return

    def rslt_snd(self):
        print("STARTING {}".format(current_thread().getName()))
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                result: Command = self._Q_CMDRSLT.get_nowait()
            except Empty:
                continue
            else:
                print("[{}]-[RCV]: DISPATCHING RESULT: {}...".format(current_thread().getName(), result.data.hex()))
                self.dispatch(result)

        print("[{}]-[SIG]: SHUT DOWN...".format(current_thread().getName()))
        return

    # hub commands
    def requestNotifications(self):
        self._dev.writeCharacteristic(0x0f, b'\x01\x00', True)
        return

    def setOfficialName(self):
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        return

    def shutDown(self):
        self._dev.disconnect()

    def reqMotorNotif(self):
        print("sending cmd1")
        n: Command = Command(bytes.fromhex('0a004101020100000001'), 0x01, True)
        self._cmdQ.put(n)
        n: Command = Command(bytes.fromhex('0c0081011109000a64647f03'), 0x01, True)
        self._cmdQ.put(n)
        n: Command = Command(bytes.fromhex('0c0081001109000a64647f03'), 0x00, True)
        self._cmdQ.put(n)
        return

    def reqMo(self):
        print("sending cmd2")
        n: Command = Command(bytes.fromhex('0a004100020100000001'), 0x00, True)
        self._cmdQ.put(n)
        return
