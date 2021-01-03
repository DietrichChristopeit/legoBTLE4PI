import threading
from abc import ABC, abstractmethod
from time import sleep

from bluepy import btle
from bluepy.btle import Peripheral

from Geraet.Motor import Motor, EinzelMotor, KombinierterMotor
from Konstanten.Anschluss import Anschluss
from MessageHandling.Pipeline import Pipeline
from MessageHandling.PubDPSub import Publisher


class Controller(ABC, abstractmethod):

    @abstractmethod
    def initialisiereController(self, kennzeichen) -> bool:
        raise NotImplementedError

    @abstractmethod
    def konfiguriereAnschlussFuer(self, motor: Motor) -> bool:
        raise NotImplementedError


stop_flag: bool = False
data = None


class HubNo2(Controller, ABC):
    """Mit dieser Klasse wird ein neuer Controller des Typs HubType 2 für das Lego-Modell erzeugt. Es gibt auch andere
            Controller, z.B. WeDo2 oder Move HubType etc..
    """

    def __init__(self, name: str, kennzeichen: str, withDelegate: bool = False):
        """Initialisierungsmethode zur Erzeugung eines HubNo2.

        :param kennzeichen:
            Dieser Parameter ist die sog. MAC-Adresse (z.B. 90:84:2B:5E:CF:1F) des Controllers.
        :param withDelegate:
            Setzt man den Parameter bei der Erzeugung des HubNo2 auf True, so können Rückmeldungen der Sensoren (Motoren,
            Neigungssensoren etc.) empfangen werden.
        """
        self._controllerName = name
        self._kennzeichen = kennzeichen
        self._withDelegate = withDelegate

        self._registrierteMotoren = []
        self._pipeline = Pipeline()

        self._controller = btle.Peripheral(kennzeichen)
        self._controllerName = self.controller.readCharacteristic(int(0x07))

        if self._withDelegate:
            self._allgemeinerNachrichtenEmpfaenger = Publisher(self._name, self._pipeline)
            self.startListenEvents()
            self._controller.writeCharacteristic(0x0f, b'\x01\x00')

    def initialisiereController(self, kennzeichen) -> bool:
        if self._controller.getState() != 'conn':
            self._controller.connect(kennzeichen)
            self._controllerName = self.controller.readCharacteristic(int(0x07))
            if self.withDelegate:
                self._controller.withDelegate(self._allgemeinerNachrichtenEmpfaenger)
                self.startListenEvents()
                self._controller.writeCharacteristic(0x0f, b'\x01\x00')
            return True
        return False

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
        self._registrierteMotoren = motoren

    @registrierteMotoren.deleter
    def registrierteMotoren(self):
        del self._registrierteMotoren

    @property
    def controller(self) -> Peripheral:
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controllers zurück.

        :return:
            self.controller

        :returns:
            Verweis auf den HubType
        """
        return self._controller

    @property
    def controllerName(self):
        """Diese Funktion (a.k.a. Methode) gibt den Namen des Controller zurück.

        :return:
            self._controllerName
        :returns:
            Der Name des Controllers wird zurückgegeben.
        """
        return self._controllerName

    def registriere(self, motor: Motor):
        """Mit dieser Funktion (a.k.a Methode) werden die am Controller angeschlossenen Motoren in einer Liste registriert.

        :param motor:
            Der MotorTyp wird in eine Liste auf dem Controller eingetragen.
        :return:
            None
        """

        port = bytes.fromhex('ff')

        if motor.anschluss is None:
            self.konfiguriereGemeinsamenAnschluss(motor)

        self.registrierteMotoren.append(motor)

        if isinstance(motor.anschluss, Anschluss):
            port = '{:02x}'.format(motor.anschluss.value)
        else:
            port = motor.anschluss

        abonniereNachrichtenFuerMotor = int(bytes.fromhex('0a0041{}020100000001'.format(port)))
        self.fuehreBefehlAus(abonniereNachrichtenFuerMotor, mitRueckMeldung=True)

    def konfiguriereGemeinsamenAnschluss(self, motor: Motor):
        """Ein synchronisierter Motor, welcher aus zwei EinzelMotoren besteht, muss zunächst konfiguriert werden. Dazu teilt
        man dem Controller (hier HubNo2) mittels des Befehls 0x61, SubBefehl 0x01, die Anschlussnummern (PortIDs) der beiden
        einzelnen Motoren mit.

        :param motor:
            Der zu konfigurierende gemeinsame Motor.
        :return: None
        """
        global data

        if isinstance(motor, (EinzelMotor, KombinierterMotor)):
            definiereGemeinsamenMotor = int(bytes.fromhex('06006101' + '{:02x}'.format(motor.anschluss.value) + '{:02x}'.format(
                    motor.anschluss.value)))
            self.fuehreBefehlAus(definiereGemeinsamenMotor, mitRueckMeldung=True)

            while self._allgemeinerNachrichtenEmpfaenger.vPort is None:
                sleep(0.5)

            if ('{:02x}'.format(self.allgemeinerNachrichtenEmpfaenger.vPort1)=='{:02x}'.format(motor.anschluss.value)) and (
                    '{:02x}'.format(
                            self.allgemeinerNachrichtenEmpfaenger.vPort2)=='{:02x}'.format(motor.anschluss.value)):
                print('WEISE GEMEINSAMEN PORT {:02x} FÜR MOTOREN {:02x} und {:02x} ZU'.format(
                    self.allgemeinerNachrichtenEmpfaenger.vPort,
                    motor.anschluss.value,
                    motor.anschluss.value))
                print('CMD:', '0a0041{:02x}020100000001'.format(self.allgemeinerNachrichtenEmpfaenger.vPort))
                abonniereNachrichtenFuerMotor = int(bytes.fromhex('0a0041{:02x}020100000001'.format(
                        self.allgemeinerNachrichtenEmpfaenger.vPort)))
                self.fuehreBefehlAus(abonniereNachrichtenFuerMotor)
                print("ABONNIERE Gemeinsamen Port", self.allgemeinerNachrichtenEmpfaenger.vPort)
                motor.anschluss = '{:02x}'.format(self.allgemeinerNachrichtenEmpfaenger.vPort)

    def fuehreBefehlAus(self, befehl: int, mitRueckMeldung: bool = True):
        self.controller.writeCharacteristic(0x0e, befehl, mitRueckMeldung)

    def event_loop(self):
        global stop_flag

        while not stop_flag:  # Schleife für das Warten auf MessageHandling
            if self.controller.waitForNotifications(1.0):
                continue
        print('.', end='')
        print('Thread Message: Notification Thread Tschuess!')

    def startListenEvents(self) -> None:
        global stop_flag

        self.notif_thr = threading.Thread(target=self.event_loop)  # Event Loop als neuer Thread
        self.notif_thr.start()

    def schalteAus(self) -> None:
        global stop_flag
        stop_flag = True
        self.controller.disconnect()
