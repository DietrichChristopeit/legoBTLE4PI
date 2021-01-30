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

from multiprocessing import Condition, Event, Process, Queue
from queue import Empty, Full
from random import uniform
from time import sleep

from LegoBTLE.Device.messaging import Message


class PMotor:
    
    def __init__(self, port: int = 0x00, Q_CMD: Queue = None, terminate: Event = None):
        self._port = port
        self._recQ: Queue = Queue()
        self._terminate: Event = terminate
        self._Q_CMD_snd: Queue = Q_CMD
        self._sendWaitQ: Queue = Queue()
        self._C_PORTFREE: Condition = Condition()
        self._E_PORTFREE: Event = Event()
        self._E_PORTFREE.set()
        return
    
    @property
    def recQ(self) -> Queue:
        return self._recQ
    
    @property
    def port(self) -> int:
        return self._port
    
    def send(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            
            with self._C_PORTFREE:
                try:
                    m = self._sendWaitQ.get_nowait()
                    print("[{}]-[MSG]: WAITING TO SEND {}...".format(name, m))
                    self._C_PORTFREE.wait_for(lambda: self._E_PORTFREE.is_set() or self._terminate.is_set())
                    self._E_PORTFREE.clear()
                    print("[{}]-[SND]: LOCKING PORT 0x{:02}...".format(name, self._port))
                    print("[{}]-[SND]: SENDING {}...".format(name, m))
                    # sleep(uniform(.01, .05))
                    self._Q_CMD_snd.put(m)
                except Empty:
                    pass
                finally:
                    self._C_PORTFREE.notify_all()
        
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def receive(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            
            with self._C_PORTFREE:
                try:
                    m = self._recQ.get_nowait()
                    print("[{}]-[RCV]: Received {}...".format(name, m))
                    if m[2] == 5:
                        self._E_PORTFREE.set()
                        print("[{}]-[RCV]: freeing PORT 0x{:02}...".format(name, m[0][1]))
                except Empty:
                    pass
                finally:
                    self._C_PORTFREE.notify_all()
        
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def command(self, cmd: int):
        MotorCmd = (cmd, self._port)
        self._sendWaitQ.put(MotorCmd)
        return


class PHub:
    
    def __init__(self, address: str = '90:84:2B:5E:CF:1F', Q_CMD: Queue = None, terminate: Event = None):
        self._terminate: Event = terminate
        self._Q_CMD_rcv: Queue = Q_CMD
        self._Q_CMDRSLT: Queue = Queue()
        self._registeredMotors: [PMotor] = []
        self._BTLEDelegate = self.BTLEDelegate(self._Q_CMDRSLT)
        self._dev: btle.Peripheral = btle.Peripheral(address)
        self._dev.withDelegate(self._BTLEDelegate)
        return
    
    class BTLEDelegate(btle.DefaultDelegate):
        
        def __init__(self, Q_CMDRSLT: Queue):
            btle.DefaultDelegate.__init__(self)
            self._Q_CMDRSLT: Queue = Q_CMDRSLT
            return
        
        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            try:
                m: Message = Message(bytes.fromhex(data.hex()), data[3].hex())
                self._Q_CMDRSLT.put_nowait(m)
            except Full:
                print("Collision...")
                pass
            return
    
    def listenNotifications(self, name):
        while not self._terminate.is_set():  # Schleife für das Warten auf Notifications
            if self._dev.waitForNotifications(1.0):
                continue
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def register(self, motor: PMotor):
        self._registeredMotors.append(motor)
        return
    
    def dispatch(self, name: str, cmd: Message):
        for m in self._registeredMotors:
            if m.port == cmd.port:
                sleep(uniform(.001, .009))
                m.recQ.put(cmd)
        return
    
    def receive(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            m = self._Q_CMD_rcv.get()
            print("[{}]-[RCV]: CMD RECEIVED: {}...".format(name, m))
            # sleep(uniform(.01, .09))
        
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def send(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            m: Message = Message()
            try:
                m = self._Q_CMDRSLT.get_nowait()
            except Empty:
                print("[{}]-[RCV]: REPLY SENDING: {}...".format(name, m))
                # sleep(uniform(.01, .09))
                self.dispatch(name, m)
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return


def shutdown(t: int, terminate: Event):
    sleep(t)
    terminate.set()
    return


def startsys(systm: []) -> []:
    r: [] = []
    i = 0
    for s in systm:
        r.append(Process(name="{}".format(i), target=s.rslt_snd, args=("{} SENDER".format(i),), daemon=True))
        r.append(Process(name="{}".format(i), target=s.res_rcv, args=("{} RECEIVER".format(i),), daemon=True))
        i = i + 1
    
    for e in r:
        e.start()
    return r


def stopsys(rt: [Process], terminate: Event):
    if terminate.is_set():
        for r in rt:
            r.join(timeout=2)
            print("EXITCODE: {}:{}".format(r.name, r.exitcode))
    return


if __name__ == "__main__":
    
    terminate: Event = Event()
    msgQ: Queue = Queue()
    st: [] = []
    hub: PHub = PHub(Q_CMD=msgQ, terminate=terminate)
    motor0: PMotor = PMotor(port=0x00, Q_CMD=msgQ, terminate=terminate)
    motor1: PMotor = PMotor(port=0x01, Q_CMD=msgQ, terminate=terminate)
    motor2: PMotor = PMotor(port=0x02, Q_CMD=msgQ, terminate=terminate)
    motor3: PMotor = PMotor(port=0x03, Q_CMD=msgQ, terminate=terminate)
    hub.register(motor3)
    hub.register(motor2)
    hub.register(motor1)
    hub.register(motor0)
    st.append(motor0)
    st.append(motor1)
    st.append(motor2)
    st.append(motor3)
    st.append(hub)
    
    shtd: Process = Process(name="SHTD PROCESS", target=shutdown, args=(10, terminate), daemon=True)
    notificationListener: Process = Process(name="HUB NOTIFICATION LISTENER", target=hub.listenNotifications,
                                            args=("HUB NOTIFICATION LISTENER",), daemon=True)
    notificationListener.start()
    shtd.start()
    rt = startsys(st)
    rt.append(shtd)
    
    for i in range(1, 200):
        motor0.command(i)
    
    for j in range(300, 500):
        motor1.command(j)
    
    for k in range(600, 800):
        motor2.command(k)
    
    for m in range(900, 1100):
        motor2.command(m)
    
    print("[MAIN]: Waiting...")
    terminate.wait()
    
    stopsys(rt, terminate)
