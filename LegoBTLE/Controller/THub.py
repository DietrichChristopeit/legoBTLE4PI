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

from LegoBTLE.Debug.messages import BBG, BBR, DBB, DBG, DBR, DBY, MSG
from LegoBTLE.Device.messaging import M_Event, M_Type, Message
from LegoBTLE.Device.TMotor import Motor


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None,
                 terminate: Event = None, debug: bool = False):
        self._E_HUB_NOFIFICATION_RQST_DONE: Event = Event()
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._Q_result: Queue = Queue(maxsize=-1)
        self._E_TERMINATE: Event = terminate

        self._debug = debug
        MSG((self._name, self._address), msg="[{}]-[MSG]: TRYING TO CONNECT TO {}...", doprint=True, style=DBY())
        self._dev: btle.Peripheral = btle.Peripheral(address)
        MSG((self._name, self._address), msg="[{}]-[MSG]: CONNECTION SUCCESSFUL TO {}...", doprint=True, style=DBG())
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        MSG((self._name, self._officialName), msg="[{}]-[MSG]: OFFICIAL NAME: {}", doprint=True, style=DBB())
        self._registeredDevices = []

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
                m: Message = Message(bytes.fromhex(data.hex()), True)
                self._Q_BCMDRSLT.put(m)
            except Full:
                MSG((), msg="Collision...", doprint=True, style=DBR())
                pass
            return

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    @property
    def r_d(self):
        return self._registeredDevices

    def listenNotif(self):
        MSG((current_thread().getName(),), msg="[{}]-[SIG]: STARTED...", doprint=True, style=BBG())
        while not self._E_TERMINATE.is_set():  # waiting loop for notifications from Hub
            # if self._dev.waitForNotifications(1.0):
            #  continue
            try:
                if self._dev.waitForNotifications(.02):
                    continue
            except BTLEInternalError:
                continue
        MSG((current_thread().getName(),), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return

    def register(self, motor: Motor):
        could_update: bool = False
        MSG((motor.name, motor.port), msg="[HUB]-[MSG]: REGISTERING {} / PORT: {}", doprint=self._debug, style=DBG())
        for rm in self._registeredDevices:
            if rm['port'] == motor.port:
                rm['device'] = motor
                could_update = True
        if could_update:
            return
        else:
            self._registeredDevices.append(({'port': motor.port, 'hub_event': M_Event.IO_DETACHED, 'device': motor}))
        return

    def rslt_snd(self):
        MSG((current_thread().getName(), ), msg="[{}]-[MSG]: STARTING...", doprint=True, style=BBG())
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                result: Message = self._Q_CMDRSLT.get_nowait()
            except Empty:
                continue
            else:
                MSG((current_thread().getName(), result.data.hex()), msg="[{}]-[RCV]: DISPATCHING RESULT: {}...",
                    doprint=True, style=DBY())
                self.dispatch(result)
    
        MSG((current_thread().getName(), ), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return
    
    def dispatch(self, cmd: Message):
        couldPut: bool = False
      
        for m in self._registeredDevices:
            if m['port'] == cmd.port:
                if (m['hub_event'] in (b'\x01', b'\x02')) and (m['device'] is not None):
                    MSG((current_thread().getName(), m['motor'].name, m['port'].hex(), cmd.data.hex()),
                        msg="[{}]-[SND] --> [{}]-[{}]: RSLT = {}", doprint=True, style=BBG())
                    m.Q_rsltrcv_RCV.put(cmd)
                    couldPut = True
        if not couldPut:
            if cmd.m_type.value == M_Type.DEVICE:
                self._registeredDevices.append(({'port': cmd.port, 'hub_event': cmd.event, 'device': None}))
            else:
                print("BLAHBLAH {}".format(cmd.data.hex()))  # something more sophisticated here
            MSG((current_thread().getName(),
                 cmd.data.hex()), msg="[{}:DISPATCHER]-[MSG]: non-dispatchable Notification {}",
                doprint=self._debug, style=DBR())
        else:
            print("COUILD PUT {}".format(cmd.data.hex()))
        return

    def res_rcv(self):
        MSG((current_thread().getName(), ), msg="[{}]-[MSG]: STARTING...", doprint=True, style=BBG())
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                command: Message = self._cmdQ.get_nowait()
                print("COMMAND:", command)
            except Empty:
                pass
            else:
                MSG((current_thread().getName(), command.port.hex(), command.data.hex()), doprint=True,
                    msg="[{}]-[RCV] <-- [{}]-[SND]: CMD RECEIVED: {}...", style=DBB())
                self._dev.writeCharacteristic(0x0e, command.data, True)

        MSG((current_thread().getName(), ), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return

    # hub commands
    def requestNotifications(self):
        self._dev.writeCharacteristic(0x0f, b'\x01\x00', True)
        self._E_HUB_NOFIFICATION_RQST_DONE.clear()
        return

    def setOfficialName(self):
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        return

    def shutDown(self):
        self._dev.disconnect()
