import threading
from abc import ABC, abstractmethod
from time import sleep

from bluepy.btle import Peripheral

from Geraet.Motor import Motor, EinzelMotor, KombinierterMotor
from Konstanten.Anschluss import Anschluss
from MessageHandling.Pipeline import Pipeline


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


stop_flag: bool = False
data = None


class HubNo2(Controller, Peripheral):
    """Mit dieser Klasse wird ein neuer Controller des Typs HubType 2 für das Lego-Modell erzeugt. Es gibt auch andere
            Controller, z.B. WeDo2 oder Move HubType etc..
    """

    def __init__(self, eigenerName: str, kennzeichen: str, delegate, messageQueue: Pipeline = None):
        """Initialisierungsmethode zur Erzeugung eines HubNo2.

        :param kennzeichen:
            Dieser Parameter ist die sog. MAC-Adresse (z.B. 90:84:2B:5E:CF:1F) des Controllers.
        :param delegate:
            Setzt man den Parameter bei der Erzeugung des HubNo2 auf True, so können Rückmeldungen der Sensoren (Motoren,
            Neigungssensoren etc.) empfangen werden.
        """
        super(HubNo2, self).__init__(kennzeichen)
        self._controllerEigenerName = eigenerName
        self._kennzeichen = kennzeichen
        self._notification = None

        self._registrierteMotoren = []
        self._pipeline = messageQueue

        self._controllerName = self.readCharacteristic(int(0x07))

        if delegate is not None:
            self.withDelegate(delegate)
            # self._allgemeinerNachrichtenEmpfaenger = Publisher(self._name, self._pipeline)
            self.writeCharacteristic(0x0f, b'\x01\x00')

    def receiveNotification(self, event: threading.Event):
        while not event.is_set() or not self._pipeline.empty():
            self._notification = self._pipeline.get_message(self._controllerEigenerName)

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

        abonniereNachrichtenFuerMotor = bytes.fromhex('0a0041{}020100000001'.format(port))
        self.fuehreBefehlAus(abonniereNachrichtenFuerMotor, mitRueckMeldung=True)

    def konfiguriereGemeinsamenAnschluss(self, motor: Motor):
        """Ein synchronisierter KMotor, welcher aus zwei EinzelMotoren besteht, muss zunächst konfiguriert werden. Dazu teilt
        man dem Controller (hier HubNo2) mittels des Befehls 0x61, SubBefehl 0x01, die Anschlussnummern (PortIDs) der beiden
        einzelnen Motoren mit.

        :param motor:
            Der zu konfigurierende gemeinsame KMotor.
        :return: None
        """
        global data

        if isinstance(motor, (EinzelMotor, KombinierterMotor)):
            definiereGemeinsamenMotor = bytes.fromhex('06006101' + '{:02x}'.format(motor.anschluss.value) + '{:02x}'.format(
                    motor.anschluss.value))
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
                abonniereNachrichtenFuerMotor = bytes.fromhex('0a0041{:02x}020100000001'.format(
                        self.allgemeinerNachrichtenEmpfaenger.vPort))
                self.fuehreBefehlAus(abonniereNachrichtenFuerMotor)
                print("ABONNIERE Gemeinsamen Port", self.allgemeinerNachrichtenEmpfaenger.vPort)
                motor.anschluss = '{:02x}'.format(self.allgemeinerNachrichtenEmpfaenger.vPort)

    def fuehreBefehlAus(self, befehl: bytes, mitRueckMeldung: bool = True):
        self.writeCharacteristic(0x0e, befehl, mitRueckMeldung)

    def schalteAus(self) -> None:
        self.controller.disconnect()
