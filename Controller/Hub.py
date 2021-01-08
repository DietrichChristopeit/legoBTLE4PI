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
import concurrent.futures
import logging
import threading
from abc import ABC, abstractmethod
from time import sleep

from bluepy.btle import Peripheral

from Geraet.Motor import Motor, EinzelMotor, KombinierterMotor
from Konstanten.Anschluss import Anschluss
from MessageHandling.MessageQueue import MessageQueue
from MessageHandling.PubDPSub import PublishingDelegate


class Controller(ABC):

    @abstractmethod
    def registriere(self, motor: Motor) -> None:
        raise NotImplementedError

    @abstractmethod
    def konfiguriereGemeinsamenAnschluss(self, motor: Motor) -> None:
        raise NotImplementedError

    @abstractmethod
    def fuehreBefehlAus(self, befehl: bytes, mitRueckMeldung: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    def schalteAus(self) -> None:
        raise NotImplementedError


class HubNo2(Controller, Peripheral):
    """Mit dieser Klasse wird ein neuer HubNo2 des Typs Controller & Peripheral für das Lego-Modell erzeugt. Es gibt auch andere
            Controller, z.B. WeDo2 oder Move HubType etc..
    """

    def __init__(self, eigenerName: str, kennzeichen: str, withDelegate: bool = True):
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

        self._pipeline = MessageQueue()
        self._notification = PublishingDelegate(friendlyName="Hub2.0 Publishing Delegate", pipeline=self._pipeline)
        self._withDelegate = withDelegate
        self._registrierteMotoren = [Motor]
        self._event = threading.Event()
        self._notif_thr = None
        self._message = ''
        if self._withDelegate:
            self._notif_thr = threading.Thread(target=self.event_loop, args={self._pipeline, self._event})  # Event Loop als neuer Thread

        self._controllerEigenerName = eigenerName
        self._kennzeichen = kennzeichen  # MAC-Adresse des Hub

    def event_loop(self, pipeline: MessageQueue, event):

        while not event.is_set():  # Schleife für das Warten auf Notifications
            if self.controller.waitForNotifications(1.0):
                self._message = pipeline.get_message("[HUB]-[RCV]")
                print("[HUB]-[RCV]: {}".format(str(self._message)))
                for m in self._registrierteMotoren:
                    m.pipeline.set_message(self._message, "[HUB]-[SND]")
                continue
            print('.', end='')
        print('[HUB]-[MSG]: mQueue shutting down... exiting...')

    def start(self) -> bool:
        if self._notif_thr is not None:
            self.withDelegate(self._notification)
            self._notif_thr.start()
            self.writeCharacteristic(0x0f, b'\x01\x00')  #subscribe to general HUB Notifications
            return True
        else:
            return False

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
    def registrierteMotoren(self) -> [Motor]:
        return self._registrierteMotoren

    @registrierteMotoren.setter
    def registrierteMotoren(self, motoren: [Motor]):
        ("\n"
         "\n"
         "        :type motoren: object\n"
         "        ")
        self._registrierteMotoren = motoren

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

    def registriere(self, motor: Motor):
        """Mit dieser Funktion (a.k.a Methode) werden die am Controller angeschlossenen Motoren in einer Liste registriert.

        :param motor:
            Der Motor wird in eine Liste auf dem Controller eingetragen.
        :return:
            None
        """

        port = bytes.fromhex('ff')
        motorPipeline = MessageQueue(debug=False, maxsize=20)

        if isinstance(motor, EinzelMotor):
            newMotor = EinzelMotor(motorPipeline, self._event, motor.anschluss, motor.uebersetzung, motor.nameMotor)
        elif isinstance(motor, KombinierterMotor):
            newMotor = KombinierterMotor(motorPipeline, self._event, motor.anschluss, motor.ersterMotorAnschluss, motor.zweiterMotorAnschluss, motor.uebersetzung, motor.nameMotor)
            self.konfiguriereGemeinsamenAnschluss(...)
        self._registrierteMotoren.append(newMotor)
        newMotor.start()

        abonniereNachrichtenFuerMotor = bytes.fromhex('0a0041{}020100000001'.format(port))
        self.fuehreBefehlAus(abonniereNachrichtenFuerMotor, mitRueckMeldung=True)


    def konfiguriereGemeinsamenAnschluss(self, motor: Motor):
        """Ein synchronisierter Motor, welcher aus zwei EinzelMotoren besteht, muss zunächst konfiguriert werden. Dazu teilt
        man dem Controller (hier HubNo2) mittels des Befehls 0x61, SubBefehl 0x01, die Anschlussnummern (PortIDs) der beiden
        einzelnen Motoren mit.

        :param motor:
            Der zu konfigurierende gemeinsame Motor.
        :return: None
        """

        if isinstance(motor, KombinierterMotor):
            definiereGemeinsamenMotor = bytes.fromhex(
                '06006101' + '{:02x}'.format(motor.ersterMotorPort) + '{:02x}'.format(
                    motor.zweiterMotorPort))
            motor.start()
            self.fuehreBefehlAus(definiereGemeinsamenMotor, mitRueckMeldung=True)
# stimmt noch nicht
            while '{:02}'.format(motor.anschluss) == '{:02x}'.format(motor.ersterMotorPort) + '{:02x}'.format(
                    motor.zweiterMotorPort):
                sleep(0.5)

            if ('{:02x}'.format(self.) == '{:02x}'.format(
                    motor.anschluss.value)) and (
                    '{:02x}'.format(
                        self.allgemeinerNachrichtenEmpfaenger.vPort2) == '{:02x}'.format(motor.anschluss.value)):
                print('WEISE GEMEINSAMEN PORT {:02x} FÜR MOTOREN {:02x} und {:02x} ZU'.format(
                    self.allgemeinerNachrichtenEmpfaenger.vPort,
                    motor.anschluss.value,
                    motor.anschluss.value))
                print('CMD:', '0a0041{:02x}020100000001'.format(self.allgemeinerNachrichtenEmpfaenger.vPort))
                abonniereNachrichtenFuerMotor = bytes.fromhex('0a0041{:02x}020100000001'.format(
                    self.allgemeinerNachrichtenEmpfaenger.vPort))
                self.fuehreBefehlAus(abonniereNachrichtenFuerMotor)
                print("ABONNIERE Gemeinsamen Port", self.allgemeinerNachrichtenEmpfaenger.vPort)
                motor.anschluss = '{:02x}'.format(self.allgemeinerNachrichtenEmpfaenger.vPort)

    def fuehreBefehlAus(self, befehl: bytes, mitRueckMeldung: bool = True):
        self.writeCharacteristic(0x0e, befehl, mitRueckMeldung)

    def handler(self, signal_received, frame):
        # Handle any cleanup here
        print('SIGINT or CTRL-C detected. Shutting Message-Threads down..')
        self._event.set()
        while self._notif_thr.is_alive():
            self._notif_thr.join(2)
        self.schalteAus()

    def schalteAus(self) -> None:
        self.controller.disconnect()
