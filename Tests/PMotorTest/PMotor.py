from multiprocessing import Process, Event, Queue, Pipe


# MIT License
#
#    Copyright (c) 2021 Dietrich Christopeit
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in all
#    copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.
#
from multiprocessing.connection import Connection
from queue import Empty, Full
from random import uniform
from time import sleep


class PHub:
    
    def __init__(self, sendQ: Queue, recCmd: Connection, terminate: Event):
        self._sendQ: Queue = sendQ
        self._terminate: Event = terminate
        self._recCmd: Connection = recCmd
        return
        
    def receive(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            if self._recCmd.poll():
                m = self._recCmd.recv()
                print("[{}]-[RCV]: CMD RECEIVED: {}".format(name, m))
                sleep(uniform(.01, .09))
                self._sendQ.put("[{}]-[SND]:RETURN CMD: {}".format(name, m))

        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    

class PMotor:
    
    def __init__(self, recQ: Queue, sendCmd: Connection, terminate: Event):
        self._recQ: Queue = recQ
        self._terminate: Event = terminate
        self._sendCmd: Connection = sendCmd
        self._sendWaitQ: Queue = Queue()
        return
    
    def send(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            try:
                m = self._sendWaitQ.get_nowait()
                print("[{}]-[SND]: SENDING...{}".format(name, m))
                sleep(uniform(.01, .05))
                self._sendCmd.send(m)
            except Empty:
                pass
        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def receive(self, name: str):
        while not self._terminate.is_set():
            if self._terminate.is_set():
                break
            try:
                m = self._recQ.get_nowait()
                print("[{}]-[RCV]: Receiving {}".format(name, m))
            except Empty:
                pass
            # sleep(uniform(1.0, 3.0))

        print("[{}]-[SIG]: SHUT DOWN...".format(name))
        return
    
    def command(self, cmd: str):
        self._sendWaitQ.put(cmd)
        return
    
    
if __name__ == "__main__":
    
    terminate: Event = Event()
    msgQ: Queue = Queue()
    s, r = Pipe()
    
    motor: PMotor = PMotor(recQ=msgQ, sendCmd=s, terminate=terminate)
    hub: PHub = PHub(sendQ=msgQ, recCmd=r, terminate=terminate)
    hubRCVP: Process = Process(name="HUB PROCESS", target=hub.receive, args=("HUB RECEIVER", ), daemon=True)
    sendP: Process = Process(name="SEND PROCESS", target=motor.send, args=("MOTOR SENDER", ), daemon=True)
    recP: Process = Process(name="REC PROCESS", target=motor.receive, args=("MOTOR RECEIVER", ), daemon=True)
    hubRCVP.start()
    sendP.start()
    recP.start()
    
    for i in range(1, 200):
        motor.command("CMD {}".format(i))
        
    print("[MAIN]: Waiting...")
    sleep(10)
    terminate.set()
    sendP.join(timeout=10)
    print("[MAIN]:SENDER SHUT DOWN")
    hubRCVP.join(timeout=10)
    print("[MAIN]:HUB SHUT DOWN")
    recP.join(timeout=10)
    print("[MAIN]:RECEIVER SHUT DOWN")
    
    print("[MAIN]:SHUT DOWN...")