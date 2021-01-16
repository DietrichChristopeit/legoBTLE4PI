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

from threading import Thread, Event

from LegoBTLE.MessageHandling.MessageQueue import *


class MotorThread(Thread):

    def __init__(self, motor: Motor, pipeline: MessageQueue, motor_event: threading.Event, cel: threading.Event):
        super().__init__()
        self._motor = motor
        self._name = motor.name
        self._pipeline = pipeline
        self._event = threading.Event()
        self._motor_event = motor_event
        self._cel = cel

    @property
    def name(self):
        return self._name

    @property
    def event(self) -> Event:
        return self._event

    def schalte_Aus(self):
        self._event.set()

    def run(self):
        while not self._event.is_set():
            if not self._pipeline.empty():
                self.listenMessageQueue()
                continue
        print("[MOTOR]-[MSG]: MOTOR {} SHUTTING DOWN...".format(self._motor.name))
        return

    def listenMessageQueue(self):
        """Mit dieser Methode werden die Notifications behandelt.

        :return:
        """

        message = bytes.fromhex(self._pipeline.get_message())
        # print("[MOTOR]-[RCV]: Message: {} Port: {}".format(message[3], self._motor.port.value))
        if message[3] == self._motor.port.value:
            print("[MOTOR]-[RCV]: Habe für Port {:02} die Nachricht {} erhalten".format(message[3], message))
            self.processMessage(message)

    def processMessage(self, message):
        if message[2] == 0x45:
            self._motor.previousAngle = self._motor.currentAngle
            self._motor.currentAngle = int(''.join('{:02x}'.format(m) for m in message[4:7][::-1]), 16) / self._motor.gearRatio
        if message[2] == 0x82:
            if message[4] == 0x01:
                self._motor_event.clear()
                self._motor.status = False
            elif message[4] == 0x0a:
                self._motor_event.set()
                self._motor.status = True

    def setzeGemeinsamenAnschluss(self, message):

        if isinstance(self._motor, KombinierterMotor):
            if (message[len(message) - 1] == self._motor.zweiterMotorAnschluss) and (
                    message[len(message) - 2] == self._motor.ersterMotorAnschluss):
                print("[MOTOR]-[RCV]: Habe für Port {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                self._motor.port = message[3]
