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
import threading
from abc import ABC, abstractmethod
from time import sleep

from bluepy.btle import Peripheral
from termcolor import colored

from LegoBTLE.Device import Motor, EinzelMotor, KombinierterMotor
from LegoBTLE.Constants.Port import Port
from oldFiles.MessageQueue import MessageQueue
from LegoBTLE.MessageHandling import PublishingDelegate
from oldFiles import MotorThread


class Controller(ABC):

    @property
    def cel(self) -> threading.Event:
        raise NotImplementedError

    @abstractmethod
    def registriere(self, motor: Motor, motor_event: threading.Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def fuehreBefehlAus(self, befehl: bytes, mitRueckMeldung: bool = True, warteAufEnde: bool = False) -> None:
        raise NotImplementedError

    @abstractmethod
    def schalte_Aus(self) -> None:
        raise NotImplementedError


class HubNo2(Controller, Peripheral):
    """Mit dieser Klasse wird ein neuer HubNo2 des Typs Controller & Peripheral für das Lego-Modell erzeugt. Es gibt auch andere
            Controller, z.B. WeDo2 oder Move HubType etc..
    """

    def __init__(self, eigenerName: str, kennzeichen: str, cc: threading.Condition, withDelegate: bool = True):
        """Initialisierungsmethode zur Erzeugung eines HubNo2.

        :param kennzeichen:
            Dieser Parameter ist die sog. MAC-Adresse (z.B. 90:84:2B:5E:CF:1F) des Controllers.
        :param withDelegate:
            Setzt man den Parameter bei der Erzeugung des HubNo2 auf True (Standard), so können Rückmeldungen der Sensoren (
            Motoren, Neigungssensoren etc.) empfangen werden.
        """
        super(HubNo2, self).__init__(kennzeichen)  # connect to Hub
        self._controllerName = self.readCharacteristic(int(0x07))
        print("[HUB]-[MSG]: Connected to {}:".format(str(self._controllerName)))
        self._cc = cc
        self._pipeline = MessageQueue(debug=False, maxsize=200)
        self._notification = PublishingDelegate(name="Hub2.0 Publishing Delegate", cmdRsltQ=self._pipeline)
        self._withDelegate = withDelegate
        self._registrierteMotoren = []
        self._stop_event = threading.Event()
        self._cel = threading.Event()
        self._cel.clear()
        self._notif_thr = None
        self._message = ''
        if self._withDelegate:
            self._notif_thr = threading.Thread(target=self.event_loop, args=(self._pipeline,))  # Event Loop als
            # neuer Thread

        self._controllerEigenerName = eigenerName
        self._kennzeichen = kennzeichen  # MAC-Adresse des Hub

    @property
    def cel(self) -> threading.Event:
        return self._cel

    def celClear(self) -> bool:
        pass

    @property
    def gelOwner(self) -> int:
        if self._gil.is_set():
            return True
        else:
            return False

    def event_loop(self, pipeline: MessageQueue):

        while not self._stop_event.is_set():  # Schleife für das Warten auf Notifications
            if self.controller.waitForNotifications(4.0):
                while not pipeline.empty():
                    self._message = pipeline.get_message()
                    print("[HUB]-[RCV]: {}".format(str(self._message)))
                    if bytes.fromhex(self._message)[2] == 0x82 and bytes.fromhex(self._message)[4] == 0x0a:

                        text = colored(
                                "[HUB]-[MSG]: COMMAND ENDED...", 'green', attrs=['reverse', 'blink'])
                        print(text)
                        self._gil.set()
                        for m in self._registrierteMotoren:
                            port = 0x00
                            if isinstance(m[1].port, Port):
                                port = m[1].port.value
                            else:
                                port = m[1].port

                            if bytes.fromhex(self._message)[3] == port:
                                m[1].waitCmd.set()
                                break
                    # elif bytes.fromhex(self._message)[2] == 0x82 and bytes.fromhex(self._message)[4] == 0x01:
                    #   text = colored(
                    #          "[HUB]-[MSG]: COMMAND STARTED...", 'red', attrs=['reverse', 'blink'])
                    # print(text)
                    # self._gil.clear()
                    for m in self._registrierteMotoren:  # could be made better with finding target motor earlier
                        m[3].set_message(self._message)

                continue

        print("[NOTIFICATION]-[MSG]: received stop_event... exiting...")

    def schalte_An(self):
        if self._notif_thr is not None:
            self.withDelegate(self._notification)
            self._notif_thr.start()
            sleep(1.0)
            self.writeCharacteristic(0x0f, b'\x01\x00')  # subscribe to general HUB Notifications

    @property
    def pipeline(self):
        return self._pipeline

    @property
    def controllerName(self) -> str:
        return self._controllerName

    @controllerName.setter
    def controllerName(self, name):
        self._controllerName = name

    @property
    def registrierteMotoren(self) -> []:
        return self._registrierteMotoren

    @registrierteMotoren.deleter
    def registrierteMotoren(self):
        del self._registrierteMotoren

    @property
    def controller(self) -> Peripheral:
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controller zurück.

        :return:
            self.controller

        :returns:
            Verweis auf den HubType
        """
        return self

    def registriere(self, motor: Motor, motor_event: threading.Event):
        """Mit dieser Funktion (a.k.a Methode) werden die am Controller angeschlossenen Motoren in einer Liste registriert.

        :param motor_event:
        :param motor:
            Der Motor wird in eine Liste auf dem Controller eingetragen.
        :return:
            None
        """

        motorPipeline = MessageQueue(debug=False, maxsize=50)
        newMotorThread = MotorThread(motor, motorPipeline, motor_event, self._cel)
        self._registrierteMotoren.append([motor.name, motor, newMotorThread, motorPipeline])
        newMotorThread.start()
        sleep(2)
        if isinstance(motor, EinzelMotor):
            self._gel.clear()
            abonniereNachrichtenFuerMotor = bytes.fromhex('0a0041{:02}020100000001'.format(motor.port.value))
            self.fuehreBefehlAus(abonniereNachrichtenFuerMotor, mitRueckMeldung=True, warteAufEnde=False)
            self._gel.wait()
        if isinstance(motor, KombinierterMotor):
            self._gel.clear()
            self.fuehreBefehlAus(motor.definiereGemeinsamenMotor(), mitRueckMeldung=True, warteAufEnde=False)
            self._gel.wait()

    def fuehreBefehlAus(self, befehl: bytes, mitRueckMeldung: bool = True, warteAufEnde: bool = True):

        self.writeCharacteristic(0x0e, befehl, mitRueckMeldung)
        # self._gil.clear()
        targetMotor: Motor = None
        for m in self._registrierteMotoren:
            port = 0x00
            if isinstance(m[1].port, Port):
                port = m[1].port.value
            else:
                port = m[1].port

            if befehl[3] == port:
                targetMotor = m[1]
                m[1].waitCmd.clear()
                break

        if warteAufEnde:
            targetMotor.waitCmd.wait()
            # self._gil.wait()

    def schalte_Aus(self) -> None:
        print("\t[HUB]-[MSG]: SHUTDOWN HUB sequence initiated...")
        print("\t\t[HUB]-[MSG]: SHUTDOWN NOTIFICATION-THREAD initiated...")
        self._stop_event.set()
        sleep(2)
        self._notif_thr.join()
        print("\t\t[HUB]-[MSG]: SHUTDOWN NOTIFICATION-THREAD complete...")
        print("\t\t[HUB]-[MSG]: SHUTDOWN MOTOR_THREADS initiated...")
        for m in self._registrierteMotoren:
            m[2].schalte_Aus()
            sleep(1)
            m[2].join()
            print("\t\t\t[HUB]-[MSG]: MOTOR {} SHUT DOWN...".format(m[2].name))
        print("\t\t[HUB]-[MSG]: SHUTDOWN MOTOR_THREADS complete...")
        print("\t[HUB]-[MSG]: SHUTDOWN HUB sequence complete...")
