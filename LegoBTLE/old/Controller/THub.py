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
from collections import deque
from concurrent import futures
from threading import Event

from bluepy import btle
from bluepy.btle import BTLEInternalError

from LegoBTLE.Debug.messages import BBG, BBR, DBB, DBG, DBR, DBY, MSG
from LegoBTLE.Device.old.messaging import Message
from LegoBTLE.Device.old.AMotor import Motor


class Hub:

    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: deque = None,
                  terminate: Event = None, debug: bool = True):
        self._E_HUB_NOFIFICATION_RQST_DONE: Event = Event()
        self._address = address
        self._name = name
        self._cmdQ: deque = cmdQ
        self._Q_HUB_CMD_RETVAL: deque = deque()
        self._E_TERMINATE: Event = terminate
        
        self._debug = debug
        MSG((self._name, self._address), msg="[{}]-[MSG]: TRYING TO CONNECT TO [{}]...", doprint=True, style=DBY())
        self._dev: btle.Peripheral = btle.Peripheral(address)
        MSG((self._name, self._address), msg="[{}]-[MSG]: CONNECTION SUCCESSFUL TO [{}]...", doprint=True, style=DBG())
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        MSG((self._name, self._officialName), msg="[{}]-[MSG]: OFFICIAL NAME: [{}]", doprint=True, style=DBB())
        self._registeredDevices = []

        self._Q_BTLE_CMD_RETVAL: deque = deque()
        self._BTLE_DelegateNotifications = self.BTLEDelegate(self._Q_BTLE_CMD_RETVAL)
        self._dev.withDelegate(self._BTLE_DelegateNotifications)

        return

    class BTLEDelegate(btle.DefaultDelegate):

        def __init__(self, Q_HUB_CMD_RETVAL: deque):
            super().__init__()
            self._Q_BTLE_CMD_RETVAL: deque = Q_HUB_CMD_RETVAL
            return

        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            self._Q_BTLE_CMD_RETVAL.appendleft(Message(bytes.fromhex(data.hex())))
            return

    @property
    def dev(self) -> btle.Peripheral:
        return self._dev

    @property
    def r_d(self):
        return self._registeredDevices

    def listenNotif(self, started: futures.Future = None) -> bool:
        MSG((self._name,), msg="[{}]-[SIG]: LISTENER STARTED...", doprint=True, style=BBG())
        started.set_result(True)
        while not self._E_TERMINATE.is_set():  # waiting loop for notifications from Hub
            # if self._dev.waitForNotifications(1.0):
            #  continue
            try:
                self._dev.waitForNotifications(.0001)
                continue
            except BTLEInternalError:
                continue
        MSG((self._name,), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return True

    def register(self, motor: Motor) -> bool:
        could_update: bool = False
        MSG((motor.name, motor.port.hex()), msg="[HUB]-[MSG]: REGISTERING [{}] / PORT: [{}]", doprint=self._debug,
            style=DBG())
        for rm in self._registeredDevices:
            if rm['port'] == motor.port:
                rm['device'] = motor
                could_update = True
        if could_update:
            return True
        else:
            self._registeredDevices.append(({'port': motor.port, 'hub_event': 'IO_DETACHED', 'device': motor}))
        return True

    def rslt_RCV(self, started: futures.Future = None) -> bool:
        MSG((self._name, ), msg="[{}]-[MSG]: RESULT RECEIVER STARTED...", doprint=True, style=BBG())
        started.set_result(True)

        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                cmd_retval: Message = self._Q_BTLE_CMD_RETVAL.pop()
            except IndexError:
                Event().wait(.01)
                continue
            else:
                MSG((self._name, cmd_retval.payload.hex()), msg="[{}]-[RCV]: DISPATCHING RESULT: [{}]...",
                    doprint=True, style=DBY())
                self.dispatch(cmd_retval)
            Event().wait(.1)
        MSG((self._name, ), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return True
    
    def dispatch(self, cmd: Message) -> bool:
        couldDispatch = False

        for m in self._registeredDevices:
            if m['port'] == cmd.port: #  and (m['device'] is not None):
                MSG((self._name, m['device'].name, m['port'].hex(), cmd.m_type.decode('utf-8'), cmd.payload.hex()),
                    msg="[{}]-[SND] --> [{}]-[{}]: CMD [{}] RSLT = [{}]", doprint=True, style=BBG())

                m['device'].Q_rsltrcv_RCV.appendleft(cmd)
                couldDispatch = True

                if cmd.m_type == b'DEVICE_INIT':
                    m['hub_event'] = cmd.event
                    m['device'].E_DEVICE_INIT.set()
        if not couldDispatch:
            MSG((self._name, cmd.payload.hex()),
                msg="[{}]:[DISPATCHER]-[MSG]: non-dispatchable Notification [{}]",
                doprint=self._debug, style=DBR())
        return True

    def cmd_SND(self, started: futures.Future = None) -> bool:
        MSG((self._name, ), msg="[{}]-[MSG]: COMMAND SENDER STARTED...", doprint=True, style=BBG())
        started.set_result(True)
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                command: Message = self._cmdQ.pop()
            except IndexError:
                Event().wait(.001)
                continue
            else:
                MSG((self._name, command.port.hex(), command.m_type.decode('utf-8'),
                     command.payload.hex()),
                    doprint=True,
                    msg="[{}]-[RCV] <-- [{}]-[SND]: CMD [{}] RECEIVED: [{}]...", style=DBB())
                self._dev.writeCharacteristic(0x0e, command.payload, True)
            Event().wait(.001)
        MSG((self._name, ), doprint=True, msg="[{}]-[SIG]: SHUT DOWN...", style=BBR())
        return True

    # hub messages
    def requestNotifications(self) -> bool:
        self._dev.writeCharacteristic(0x0f, b'\x01\x00', True)
        Event().wait(5)
        return True

    def setOfficialName(self) -> bool:
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        return True

    def shutDown(self) -> bool:
        self._dev.disconnect()
        return True
