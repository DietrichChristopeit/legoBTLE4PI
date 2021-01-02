import threading
from abc import ABC, abstractmethod
from time import sleep

from bluepy import btle
from bluepy.btle import Peripheral

from Geraet.Motor import Motor, EinzelMotor, KombinierterMotor
from Konstanten.Anschluss import Anschluss
from Notifications.Notification import Notification


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

    def __init__(self, kennzeichen: str = None, withDelegate: bool = False):
        """Initialisierungsmethode zur Erzeugung eines HubNo2.

        :param kennzeichen:
            Dieser Parameter ist die sog. MAC-Adresse (z.B. 90:84:2B:5E:CF:1F) des Controllers.
        :param withDelegate:
            Setzt man den Parameter bei der Erzeugung des HubNo2 auf True, so können Rückmeldungen der Sensoren (Motoren,
            Neigungssensoren etc.) empfangen werden.
        """
        self.notif_thr = None
        self.registrierteMotoren = []
        self.withDelegate = withDelegate
        if withDelegate:
            self.rueckmeldung = Notification()

        if kennzeichen is not None:
            if withDelegate:
                self.controller = btle.Peripheral(kennzeichen)
                self.controller.withDelegate(self.rueckmeldung)
                self.startListenEvents()
                self.controller.writeCharacteristic(0x0f, b'\x01\x00')
            else:
                self.controller = btle.Peripheral(kennzeichen)
        else:
            self.controller = btle.Peripheral()

    def initialisiereController(self, kennzeichen) -> bool:
        if self.controller.getState()!='conn':
            self.controller.connect(kennzeichen)
            if self.withDelegate:
                self.controller.withDelegate(self.rueckmeldung)
                self.startListenEvents()
                self.controller.writeCharacteristic(0x0f, b'\x01\x00')
            return True
        return False

    @property
    def holeController(self) -> Peripheral:
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controllers zurück.

        :return:
            self.controller

        :returns:
            Verweis auf den HubType
        """
        return self.controller

    @property
    def leseControllerName(self):
        """Diese Funktion (a.k.a. Methode) gibt den Namen des Controller zurück.

        :return:
            self.controller.readCharacteristic(int(0x07))
        :returns:
            Der Name des Controllers wird zurückgegeben.
        """
        return self.controller.readCharacteristic(int(0x07))

    def registriere(self, motor: Motor):
        """Mit dieser Funktion (a.k.a Methode) werden die am Controller angeschlossenen Motoren in einer Liste registriert.

        :param motor: Der MotorTyp wird in eine Liste auf dem Controller eingetragen.
        :return: None
        """
        if motor.anschluss is not None:
            self.registrierteMotoren.append(motor)
            if isinstance(motor.anschluss, Anschluss):
                print('richtig')
                port = '{:02x}'.format(motor.anschluss.value)
            else:
                port = motor.anschluss
            print('CMD:', '0a0041{}020100000001'.format(port))
            self.controller.writeCharacteristic(0x0e, bytes.fromhex('0a0041{}020100000001'.format(port)))
        else:
            self.konfiguriereGemeinsamenAnschluss(motor)
            self.registrierteMotoren.append(motor)

    def konfiguriereGemeinsamenAnschluss(self, motor: Motor):
        """

        :param motor: Der zu konfigurierende MotorTyp.
        :return: None
        """
        global data

        if isinstance(motor, (EinzelMotor, KombinierterMotor)):
            command: str = '06006101' + '{:02x}'.format(motor.anschluss.value) + '{:02x}'.format(
                    motor.anschluss.value)
            self.fuehreBefehlAus(int(bytes.fromhex(command)), mitRueckMeldung=True)

            while self.rueckmeldung.vPort is None:
                sleep(0.5)

            if ('{:02x}'.format(self.rueckmeldung.vPort1)=='{:02x}'.format(motor.anschluss.value)) and ('{:02x}'.format(
                    self.rueckmeldung.vPort2)=='{:02x}'.format(motor.anschluss.value)):
                print('WEISE GEMEINSAMEN PORT {:02x} FÜR MOTOREN {:02x} und {:02x} ZU'.format(self.rueckmeldung.vPort,
                                                                                              motor.anschluss.value,
                                                                                              motor.anschluss.value))
                print('CMD:', '0a0041{:02x}020100000001'.format(self.rueckmeldung.vPort))
                self.controller.writeCharacteristic(0x0e, bytes.fromhex('0a0041{:02x}020100000001'.format(
                        self.rueckmeldung.vPort)))
                print("ABONNIERE Gemeinsamen Port", self.rueckmeldung.vPort)
                motor.anschluss = '{:02x}'.format(self.rueckmeldung.vPort)

    def fuehreBefehlAus(self, befehl: int, mitRueckMeldung: bool = True):
        self.controller.writeCharacteristic(0x0e, befehl, mitRueckMeldung)

    def event_loop(self):
        global stop_flag

        while not stop_flag:  # Schleife für das Warten auf Notifications
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
