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

from queue import Empty, Full
from multiprocessing import Process, Event, Queue
from time import sleep

from bluepy import btle
from bluepy.btle import BTLEInternalError
from colorama import Fore, Style

from LegoBTLE.Device.Command import Command
from LegoBTLE.Device.TMotor import Motor, SingleMotor, SynchronizedMotor
#from LegoBTLE.MessageHandling.TNotification import PublishingDelegate


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
            btle.DefaultDelegate.__init__(self)
            self._Q_CMDRSLT: Queue = Q_CMDRSLT
            return
        
        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            try:
                m: Command = Command(bytes.fromhex(data.hex()), data[3].hex(), True)
                self._Q_CMDRSLT.put_nowait(m)
            except Full:
                print("Collision...")
                pass
            return
        
    @property
    def dev(self) -> btle.Peripheral:
        return self._dev
    
    def listenNotifications(self, name):
        while not self._E_TERMINATE.is_set():  # waiting loop for notifications from Hub
            try:
                if self._dev.waitForNotifications(1.0):
                    continue
            except BTLEInternalError:
                pass
            
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
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
                m.Q_rsltrcv_RCV.put(cmd)
                couldPut = True
        if not couldPut:
            print("[HUB]-[MSG]: non-dispatchable Notification {}".format(cmd.data.hex()))
        return

    def receive(self, name: str):
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                command: Command = self._cmdQ.get()
            except Empty:
                continue
            else:
                print("[{}]-[RCV]: CMD RECEIVED: {}...".format(name, command.data.hex()))
                self._dev.writeCharacteristic(0x0e, command.data, True)

        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return

    def send(self, name: str):
        while not self._E_TERMINATE.is_set():
            if self._E_TERMINATE.is_set():
                break
            try:
                result: Command = self._Q_CMDRSLT.get_nowait()
            except Empty:
                continue
            else:
                print("[{}]-[RCV]: REPLY SENDING: {}...".format(name, result))
                self.dispatch(result)
                
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
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


if __name__ == '__main__':
    
    terminate: Event = Event()
    cmdQ: Queue = Queue(maxsize=-1)
    
    hub: Hub = Hub(address='90:84:2B:5E:CF:1F', name="Processed Hub", cmdQ=cmdQ, terminate=terminate, debug=True)
    
    P_NOTIFICATIONS_LISTENER: Process = Process(name="BTLE NOTIFICATION LISTENER", target=hub.listenNotifications,
                                                args=("BTLE NOTIFICATION LISTENER", ), daemon=True)
    
    P_HUB_SEND: Process = Process(name="HUB COMMAND SENDER", target=hub.send, args=("HUB COMMAND SENDER", ),
                                  daemon=True)
    
    P_HUB_RCV: Process = Process(name="HUB COMMAND RECEIVER", target=hub.receive, args=("HUB COMMAND RECEIVER", ),
                                 daemon=True)
    
    P_NOTIFICATIONS_LISTENER.start()
    P_HUB_SEND.start()
    P_HUB_RCV.start()
    
    hub.requestNotifications()
    
    sleep(20)
    
    terminate.set()
    
    P_HUB_RCV.join(2)
    P_HUB_SEND.join(2)
    P_NOTIFICATIONS_LISTENER.join(2)
    hub.shutDown()
    
    print("[{__name__}]-[MSG]: SHUTDOWN COMPLETE...")
    