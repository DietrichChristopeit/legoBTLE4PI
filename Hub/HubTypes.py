import threading
from time import sleep

from bluepy import btle
from bluepy.btle import Peripheral

from Hub.Notification import Notification
from Motor import Motor
from Motor.EinzelMotor import EinzelMotor
from Motor.KombinierterMotor import KombinierterMotor

stop_flag: bool = False
data = None


class HubNo2:
    """Mit dieser Klasse wird ein neuer Controller des Typs Hub 2 für das Lego-Modell erzeugt. Es gibt auch andere
            Controller, z.B. WeDo2 oder Move Hub etc..
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
        self.registrierteMotoren: Motor = []
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

    def verbindeMitController(self, kennzeichen):
        if self.controller.getState()!='conn':
            self.controller.connect(kennzeichen)
            if self.withDelegate:
                self.controller.withDelegate(self.rueckmeldung)
                self.startListenEvents()
                self.controller.writeCharacteristic(0x0f, b'\x01\x00')

    @property
    def holeController(self) -> Peripheral:
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controllers zurück.

        :return:
            self.controller

        :returns:
            Verweis auf den Hub
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

        :param motor: Der Motor wird in eine Liste auf dem Controller eingetragen.
        :return: None
        """
        assert (isinstance(motor, EinzelMotor) | isinstance(motor, KombinierterMotor))
        if motor.anschlussDesMotors is not None:
            self.registrierteMotoren.append(motor)
        else:
            self.konfiguriereGemeinsamenAnschluss(motor)
            self.registrierteMotoren.append(motor)

    def konfiguriereGemeinsamenAnschluss(self, motor: Motor):
        """

        :param motor: Der zu konfigurierende Motor.
        :return: None
        """
        global data

        if isinstance(motor, KombinierterMotor):
            command: str = '06006101' + '{:02x}'.format(motor.ersterMotorPort.value) + '{:02x}'.format(
                    motor.zweiterMotorPort.value)
            self.fuehreBefehlAus(bytes.fromhex(command), mitRueckMeldung=True)

            while self.rueckmeldung.vPort is None:
                sleep(0.5)

            if ('{:02x}'.format(self.rueckmeldung.vPort1)=='{:02x}'.format(motor.ersterMotorPort.value)) and ('{:02x}'.format(
                    self.rueckmeldung.vPort2)=='{:02x}'.format(motor.zweiterMotorPort.value)):
                print('WEISE GEMEINSAMEN PORT {:02x} FÜR MOTOREN {:02x} und {:02x} ZU'.format(self.rueckmeldung.vPort,
                                                                                      motor.ersterMotorPort.value,
                                                                                      motor.zweiterMotorPort.value))
                motor.weiseAnschlussZu('{:02x}'.format(self.rueckmeldung.vPort))

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
