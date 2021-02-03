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
from collections import deque
from threading import Condition, Event, Lock, current_thread
from queue import Empty

from bluepy import btle
from bluepy.btle import BTLEInternalError

from LegoBTLE.Debug.messages import BBG, BBR, DBB, DBG, DBR, DBY, MSG
from LegoBTLE.Device.messaging import Message
from LegoBTLE.Device.TMotor import Motor


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: deque = None,
                  terminate: Event = None, debug: bool = False):
        self._E_HUB_NOFIFICATION_RQST_DONE: Event = Event()
        self._address = address
        self._name = name
        self._cmdQ: deque = cmdQ
        self._Q_HUB_CMD_RETVAL: deque = deque()
        self._E_ITEM_AVAIL = Event()
        self._E_TERMINATE: Event = terminate
        
        self._debug = debug
        MSG((self._name, self._address), msg="[{}]-[MSG]: TRYING TO CONNECT TO {}...", doprint=True, style=DBY())
        self._dev: btle.Peripheral = btle.Peripheral(address)
        MSG((self._name, self._address), msg="[{}]-[MSG]: CONNECTION SUCCESSFUL TO {}...", doprint=True, style=DBG())
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        MSG((self._name, self._officialName), msg="[{}]-[MSG]: OFFICIAL NAME: {}", doprint=True, style=DBB())
        self._registeredDevices = []

        self._Q_BTLE_CMD_RETVAL: deque = deque()
        self._BTLE_DelegateNotifications = self.BTLEDelegate(self._Q_BTLE_CMD_RETVAL, self._E_ITEM_AVAIL)
        self._dev.withDelegate(self._BTLE_DelegateNotifications)

        return

    class BTLEDelegate(btle.DefaultDelegate):

        def __init__(self, Q_HUB_CMD_RETVAL: deque, E_ITEM_AVAIL: Event):
            super().__init__()
            self._Q_BTLE_CMD_RETVAL: deque = Q_HUB_CMD_RETVAL
            self._E_ITEM_AVAIL: Event = E_ITEM_AVAIL
            return

        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            l: Lock = Lock()
            l.acquire()
            m = None
            self._Q_BTLE_CMD_RETVAL.appendleft(Message(bytes.fromhex(data.hex()), True))
            self._E_ITEM_AVAIL.set()
            l.release()
            return

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    @property
    def r_d(self):
        return self._registeredDevices

    def listenNotif(self):
        MSG((current_thread().getName(),), msg="[{}]-[SIG]: STARTED...", doprint=True, style=BBG())
        notif_cond: Condition = Condition()
        while not self._E_TERMINATE.is_set():  # waiting loop for notifications from Hub
            # if self._dev.waitForNotifications(1.0):
            #  continue
            try:
                with notif_cond:
                    notif_cond.wait_for(lambda: self._dev.waitForNotifications(1.0), timeout=1.0)
                    notif_cond.notify_all()
                    continue
            except BTLEInternalError:
                continue
        MSG((current_thread().getName(),), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return

    def register(self, motor: Motor):
        could_update: bool = False
        MSG((motor.name, motor.port.hex()), msg="[HUB]-[MSG]: REGISTERING {} / PORT: {}", doprint=self._debug,
            style=DBG())
        for rm in self._registeredDevices:
            if rm['port'] == motor.port:
                rm['device'] = motor
                could_update = True
        if could_update:
            return
        else:
            self._registeredDevices.append(({'port': motor.port, 'hub_event': 'IO_DETACHED', 'device': motor}))
        return

    def rslt_RCV(self):
        MSG((current_thread().getName(), ), msg="[{}]-[MSG]: STARTING...", doprint=True, style=BBG())
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                c: Condition = Condition()
                with c:
                    c.wait_for(lambda: self._E_ITEM_AVAIL.is_set())
                    cmd_retval: Message = self._Q_BTLE_CMD_RETVAL.pop()
                    c.notify_all()
            except IndexError:
                continue
            else:
                MSG((current_thread().getName(), cmd_retval.payload.hex()), msg="[{}]-[RCV]: DISPATCHING RESULT: {}...",
                    doprint=True, style=DBY())
                self.dispatch(cmd_retval)
                
        MSG((current_thread().getName(), ), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return
    
    def dispatch(self, cmd: Message):
        couldPut: bool = False
      
        for m in self._registeredDevices:
            if (m['port'] == cmd.port) and (m['device'] is not None):
                MSG((current_thread().getName(), m['device'].name, m['port'].hex(), cmd.m_type, cmd.payload.hex()),
                    msg="[{}]-[SND] --> [{}]-[{}]: CMD [{}] RSLT = {}", doprint=True, style=BBG())
                m['device'].Q_rsltrcv_RCV.put(cmd)
                if cmd.m_type == b'DEVICE_INIT':
                    m['hub_event'] = cmd.event
                couldPut = True
        if not couldPut:
            if cmd.m_type == b'DEVICE_INIT':
                self._registeredDevices.append(({'port': cmd.port, 'hub_event': cmd.event, 'device': None}))
                MSG((current_thread().getName(), cmd.port.hex()),
                    msg="[{}]:[DISPATCHER]-[MSG]: Connection to Device added: Port [{}]",
                    doprint=self._debug, style=DBR())
            else:
                MSG((current_thread().getName(), cmd.payload.hex()),
                    msg="[{}]:[DISPATCHER]-[MSG]: non-dispatchable Notification {}",
                    doprint=self._debug, style=DBR())
        return

    def cmd_SND(self):
        MSG((current_thread().getName(), ), msg="[{}]-[MSG]: STARTING...", doprint=True, style=BBG())
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                command: Message = self._cmdQ.pop()
            except IndexError:
                Event().wait(.003)
                continue
            else:
                MSG((current_thread().getName(), command.port.hex(), command.cmd,
                     command.payload.hex()),
                    doprint=True,
                    msg="[{}]-[RCV] <-- [{}]-[SND]: CMD [{}] RECEIVED: {}...", style=DBB())
                self._dev.writeCharacteristic(0x0e, command.payload, True)

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
