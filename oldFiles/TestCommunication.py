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

#
   MIT License
  
   Copyright (c) 2021 Dietrich Christopeit
  
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
  
   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.
  
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
  

#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
import queue
import threading
from time import sleep

from LegoBTLE.Device.old import messaging
from LegoBTLE.Constants.Port import Port
from oldFiles.MessageQueue import MessageQueue
from oldFiles.TNotification import PublishingDelegate


class THub(threading.Thread):
    def __init__(self):
        """
        Models the Technic Hub as thread.
        Spawns 3 additional threads.
        """
        super().__init__()

        self._receiveQ: MessageQueue = MessageQueue()
        self._execQ: MessageQueue = MessageQueue()
        self._shutdown: threading.Event = threading.Event()
        self._notification: PublishingDelegate = PublishingDelegate(name="Hub2.0 Publishing Delegate",
                                                                    cmdRsltQ=self._receiveQ)
        self._TNotif: threading.Thread = threading.Thread(target=self.results, name="Execution Results")
        self._TExec: threading.Thread = threading.Thread(target=self.execute, name="UpStreamMessageBuilder Execution")
        self._motors: [[MessageQueue, threading.Event]] = []
        self._gcel: threading.Event = threading.Event()
        self._execLock: threading.Lock = threading.Lock()

    def terminate(self):
        self._shutdown.set()

    @property
    def gcel(self) -> threading.Event:
        return self._gcel

    @property
    def execLock(self) -> threading.Lock:
        return self._execLock

    @property
    def execQ(self) -> MessageQueue:
        return self._execQ

    @property
    def controller(self):
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controller zurück.

        :return:
            self.controller

        :returns:
            Verweis auf den HubType
        """
        return self

    def run(self):
        print("[HUB]-[MSG]: (Execution Thread): STARTING ATTEMPT...")
        self._TExec.run()
        print("[HUB]-[MSG]: (Result Notification Thread): STARTING ATTEMPT...")
        self._TNotif.run()

        self._shutdown.wait()
        print("[HUB]-[MSG]: shutting down Communication subsystems...")
        self._TNotif.join()
        self._TExec.join()
        return

    def execute(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().name))
        lastCmd: messaging = messaging(b'', 0xff, None, False)

        while True:
            if self._shutdown.is_set():
                print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().name))
                break
            else:
                cmd: messaging = self._execQ.get_message()

                if lastCmd.port == cmd.port:
                    cmd.portFree.wait()  # same as lastCmd.portFree.wait()
                    cmd.portFree.clear()
                lastCmd = cmd
                print("[{}]-[MSG]: EXECUTING COMMAND...".format(threading.current_thread().name))
                # execute WriteCharacteristic(cmd[0])
                if cmd.withWait:
                    cmd.portFree.wait()

        return

    def results(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().name))

        while True:
            if self._shutdown.is_set():
                break
            else:
                result = self._receiveQ.get_message()  # self.controller.waitForNotification(1.0)
                for motor in self._motors:
                    motor[0].set_message(result)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().name))
        return

    def register(self, motor: [MessageQueue, threading.Event]):
        """

        :param motor:
        :return:
        """
        self._motors.append(motor)
        return


class TMotor(threading.Thread):

    def __init__(self, name: str, port: Port, eHub: THub, gearRatio: float = 1.0):
        super().__init__()
        self._name = name
        self._shutdown = threading.Event()
        self._resultQ = MessageQueue(maxsize=200)
        self._execQ = eHub.execQ
        self._execLock: threading.Lock = eHub.execLock
        self._portFree = threading.Event()
        self._portFree.set()
        self._port = port.value
        self._previousAngle = 0.00
        self._currentAngle = 0.00
        self._gearRatio = gearRatio
        return

    def terminate(self):
        self._shutdown.set()
        return

    def commandA(self, withWait: bool = False):
        self._portFree.wait()
        self._portFree.clear()
        command = messaging(cmd, self._port, self._portFree, withWait)
        self._execQ.set_message(command)
        return

    def commandB(self, withWait: bool = False):
        self._portFree.wait()
        self._portFree.clear()
        command = messaging(cmd, self._port, self._portFree, withWait)
        self._execQ.set_message(command)
        return

    def commandC(self, withWait: bool = False):
        self._portFree.wait()
        self._portFree.clear()
        command = messaging(cmd, self._port, self._portFree, withWait)
        self._execQ.set_message(command)
        return

    def run(self):
        print("[{}]-[MSG]: STARTED...".format(threading.current_thread().name))

        while True:
            if self._shutdown.is_set():
                while not self._resultQ.empty():
                    remainingResults = self._resultQ.get_message()
                break
            result = bytes.fromhex(self._resultQ.get_message())
            self.processResults(result)

        print("[{}]-[MSG]: SHUTTING DOWN...".format(threading.current_thread().name))
        return

    def processResults(self, result: bytes):
        if result[2] == 0x45:
            self._previousAngle = self._currentAngle
            self._currentAngle = int(''.join('{:02x}'.format(m) for m in result[4:7][::-1]),
                                     16) / self._gearRatio
        if (result[2] == 0x82) and (result[4] == 0x0a):
            self._portFree.set()


if __name__ == '__main__':
    tTerminate = threading.Event()
    uTerminate = threading.Event()
    eTerminate = threading.Event()
    tDone = threading.Event()
    uDone = threading.Event()
    q = queue.Queue()
    r = queue.Queue()
    execQ = queue.Queue()
    cel = threading.Event()
    cel.set()
    e = MotorThread(cel)
    t = MotorThread(5, "THREAD T", 0.5, tTerminate, q, execQ, cel)
    u = MotorThread(5, "THREAD U", 0.5, uTerminate, r, execQ, cel)
    t.start()
    u.start()
    e.start()
    t.loadCMD(1, True)
    cel.wait()
    t.loadCMD(2)
    t.loadCMD(3)
    u.loadCMD(1)

    u.loadCMD(2)

    u.loadCMD(3)

    sleep(2)
    tTerminate.set()
    uTerminate.set()
    t.join()
    u.join()
    print("ABOUT TO TERMINATE...")
    t.join()
    u.join()
    print("TERMINATED")
    print("exit")
