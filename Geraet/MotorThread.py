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
from Geraet.Motor import *
from MessageHandling.MessageQueue import *
from threading import Event


class MotorThread(threading.Thread):

    def __init__(self, motor: Motor, pipeline: MessageQueue, event: Event):
        threading.Thread.__init__(self)
        self._motor = motor
        self._pipeline = pipeline
        self._event = event

    def run(self):
        self.listenMessageQueue()

    def listenMessageQueue(self):
        """Mit dieser Methode werden die Notifications behandelt.

        :param pipeline:
            Dieser Parameter stellt die Verbindung zum Hub dar. Jeder KMotor hat eine eigene Pipeline.
        :param event:
            Dieser Parameterist das Ereignis, welches gesetzt wird, wenn die Verarbeitung beendet ist.
        :return:
        """
        while not self._event.is_set():
            message = bytes.fromhex(self._pipeline.get_message(id(self)))
            if message[3] == self._motor.anschluss:
                self.processMessage(message)
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                continue
            elif isinstance(self._motor, KombinierterMotor) and (message[3] == 0x04):
                self.setzeGemeinsamenAnschluss(message)

                continue
            print('.', end='')

        while not pipeline.qsize() == 0:  # process remaining items in queue
            message = bytes.fromhex(self._pipeline.get_message(self.id))
            if message[3] == self._motor.anschluss:
                self.processMessage(message)
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                continue
        print('[MOTOR]-[MSG]: mQueue shutting down... exiting...')

    def processMessage(self, message):
        if message[2] == 0x45:
            self._motor.vorherigerWinkel = self._motor.aktuellerWinkel
            self._motor.aktuellerWinkel = int(''.join('{:02x}'.format(m) for m in message[4:7][::-1]), 16)
        if message[2] == 0x82:
            self._motor.status = message[4]

    def setzeGemeinsamenAnschluss(self, message):

        if isinstance(self._motor, KombinierterMotor):
            if (message[len(message) - 1] == self._motor.zweiterMotorAnschluss) and (
                    message[len(message) - 2] == self._motor.ersterMotorAnschluss):
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                self._motor.anschluss = message[3]
