from abc import ABC, abstractmethod

from Konstanten.Anschluss import Anschluss
from Konstanten.Motor import Motor as MotorKonstanten
from Konstanten.SI_Einheit import SI_Einheit


class Motor(ABC):
    """Abstrakte Basisklasse für alle Motoren. Design noch nicht endgültig."""

    @property
    @abstractmethod
    def nameMotor(self) -> str:
        raise NotImplementedError

    @nameMotor.setter
    @abstractmethod
    def nameMotor(self, nameMotor: str):
        raise NotImplementedError

    @nameMotor.deleter
    @abstractmethod
    def nameMotor(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def uebersetzung(self) -> float:
        raise NotImplementedError

    @uebersetzung.setter
    @abstractmethod
    def uebersetzung(self, uebersetzung: float):
        raise NotImplementedError

    @uebersetzung.deleter
    @abstractmethod
    def uebersetzung(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def anschluss(self) -> Anschluss:
        raise NotImplementedError

    @anschluss.setter
    @abstractmethod
    def anschluss(self, anschluss: Anschluss):
        raise NotImplementedError

    @anschluss.deleter
    @abstractmethod
    def anschluss(self):
        raise NotImplementedError

    def dreheMotorFuerT(self, millisekunden: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                        zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Zeit berechnen lassen.

            :rtype:
                str
            :param millisekunden:
                Die Dauer, für die der MotorTyp sich drehen soll.
            :param richtung:
                Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
                MotorKonstanten.LINKS oder
                MotorKonstanten.RECHTS).
            :param power:
                Ein Wert von 0 bis 100.
            :param zumschluss:
                Bestimmt, wie sich der MotorTyp, nachdem die Drehungen beendet wurden, verhalten soll,
                d.h. MotorKonstanten.AUSLAUFEN = der MotorTyp hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
                Stillstand;
                MotorKonstanten.BREMSEN = der MotorTyp wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht
                werden;
                MotorKonstanten.FESTHALTEN = MotorTyp wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
                den MotorTyp zu
                drehen.
            :returns:
                Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power
        zs = zumschluss.value
        befehl: str = ''

        try:
            assert self.anschluss is not None
            if isinstance(self.anschluss, Anschluss):
                port = '{:02x}'.format(self.anschluss.value)
            else:
                port = self.anschluss

            befehl: str = '0c0081{}1109'.format(port) + millisekunden.to_bytes(2, byteorder='little',
                                                                               signed=False).hex() \
                          + \
                          power.to_bytes(1, byteorder='little', signed=True).hex() + '64{}03'.format(zs.to_bytes(1,
                                                                                                                 byteorder='little',
                                                                                                                 signed=False).hex())
        except AssertionError:
            print('MotorTyp ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotorFuerGrad(self, grad: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                           zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Anzahl Grad (°) berechnen lassen.


        :param grad:
            Der Winkel in ° um den der MotorTyp, d.h. dessen Welle gedreht werden soll. Ein ganzzahliger Wert, z.B. 10,
            12, 99 etc.
        :param richtung:
            Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
            MotorKonstanten.LINKS oder
            MotorKonstanten.RECHTS).
        :param power:
            Ein Wert von 0 bis 100.
        :param zumschluss:
            Bestimmt, wie sich der MotorTyp, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. MotorKonstanten.AUSLAUFEN = der MotorTyp hält nicht sofort an sodern dreht sich aus eigener Kraft bis zum
            Stillstand;
            MotorKonstanten.BREMSEN = der MotorTyp wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
            MotorKonstanten.FESTHALTEN = MotorTyp wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den MotorTyp zu drehen.
        :rtype:
            str
        :returns:
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power
        grad = round(grad * self.uebersetzung)

        befehl: str = ''

        try:
            assert self.anschluss is not None
            if isinstance(self.anschluss, Anschluss):
                port = '{:02x}'.format(self.anschluss.value)
            else:
                port = self.anschluss
            befehl: str = '0e0081{}110b'.format(port) + grad.to_bytes(4,
                                                                      byteorder='little',
                                                                      signed=False).hex() \
                          + power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(zumschluss.value)
        except AssertionError:
            print('MotorTyp ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: int = 0, richtung: MotorKonstanten = MotorKonstanten.VOR,
                   power: int = 50, zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> bytes:
        """Diese Methode dreht einen MotorTyp, wobei der Aufrufer die Art durch die Angabe der Einheit spezifiziert.


        :rtype: 
            str
        :param SI: 
            SI-Einheit basierend auf welcher der MotorTyp gedreht werden soll (z.B. SI_Einheit.WINKEL).
        :param wertDerEinheit: 
            Um welchen Wert in der Einheit SI soll gedreht werden.
        :param richtung: 
            Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
            MotorKonstanten.LINKS oder
            MotorKonstanten.RECHTS).
        :param power: 
            Ein Wert von 0 bis 100.
        :param zumschluss: 
            Bestimmt, wie sich der MotorTyp, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. 
            * MotorKonstanten.AUSLAUFEN = der MotorTyp hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
            Stillstand; 
            * MotorKonstanten.BREMSEN = der MotorTyp wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht
            werden; 
            * MotorKonstanten.FESTHALTEN = MotorTyp wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den MotorTyp zu drehen.
        :returns: 
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        befehl: str = ''
        return bytes.fromhex(befehl)

    def reset(self) -> bytes:
        befehl: str = ''
        try:
            assert self.anschluss is not None
            if isinstance(self.anschluss, Anschluss):
                port = '{:02x}'.format(self.anschluss.value)
            else:
                port = self.anschluss
            befehl: str = '0b0081{}11510200000000'.format(port)
        except AssertionError:
            print('MotorTyp ist keinem Anschluss zugewiesen... Programmende...')
        return bytes.fromhex(befehl)


class EinzelMotor(Motor, ABC):

    def __init__(self, port: Anschluss, uebersetzung: float = 1.0, name: str = None):
        """Die Klasse EinzelMotor dient der Erstellung eines einzelnen neuen Motors.


        :type port: Anschluss
        :param port:
            Ein Anschluss, z.B. Anschluss.A .
        :param uebersetzung:
            Das Verhältnis von treibendem Zahnrad zu angetriebenem Zahnrad, Standard = 1.0 (keine Übersetzung)
        :param name:
            Eine gute Bezeichnung, die beschreibt, was der MotorTyp tun soll.
        """

        self._anschluss = port
        self._nameMotor = name
        self._uebersetzung = uebersetzung

    @property
    def nameMotor(self) -> str:
        return self._nameMotor

    @nameMotor.setter
    def nameMotor(self, nameMotor: str):
        self._nameMotor = nameMotor

    @nameMotor.deleter
    def nameMotor(self):
        del self._nameMotor

    @property
    def uebersetzung(self) -> float:
        return self._uebersetzung

    @uebersetzung.setter
    def uebersetzung(self, uebersetzung: float):
        self._uebersetzung = uebersetzung

    @uebersetzung.deleter
    def uebersetzung(self):
        del self._uebersetzung

    @property
    def anschluss(self):
        return self._anschluss

    @anschluss.setter
    def anschluss(self, anschluss: Anschluss):
        self._anschluss = anschluss

    @anschluss.deleter
    def anschluss(self):
        del self._anschluss

    def setzeZaehlwerkAufNull(self, SI: SI_Einheit):
        """Mit dieser Methode wir der Zähler für die SI-Einheit SI (z.B. SI_Einheit.WINKEL) auf 0 gesetzt. Falls eine falsche
        Einheit gewählt wird, wird eine Fehlermeldung ausgegeben und das Programm beendet.

        :param SI:
            SI-Einheit des Zählers (z.B. SI_Einheit.WINKEL).
        :return:
            Es wird kein Ergebnis zurückgegeben.
        """

        if SI==SI_Einheit.WINKEL:
            pass  # setzte Gradzähler auf 0
        elif SI==SI_Einheit.UMDREHUNG:
            pass  # setze Umdrehungszähler auf 0
        else:
            raise Exception(
                    "Der Zähler für die Einheit" + SI.value + " kann nicht zurückgesetzt werden. Falsche "
                                                              "Einheit.").with_traceback()

    def kalibriereMotor(self) -> float:
        """Mit dieser Methode wird der MotorTyp sozusagen in die Mitte gestellt.

        :rtype:
            float
        :return:
            Der maximale Winkel, den der MotorTyp in eine Richtung drehen kann.
        """

        maxWinkel = 0
        return maxWinkel


class KombinierterMotor(Motor, ABC):
    '''Kombination aus 2 (zwei) verschiedenen Motoren. Kommandos-Ausführung ist synchronisiert.
    '''

    def __init__(self, ersterMotor: EinzelMotor, zweiterMotor: EinzelMotor, uebersetzung: float = 1.0, name: str = ""):
        """

        :param ersterMotor:
        :param zweiterMotor:
        :param name:
        """
        self.ersterMotorPort = ersterMotor.anschluss
        self.zweiterMotorPort = zweiterMotor.anschluss
        self._uebersetzung = uebersetzung

        self._anschluss = None
        self._nameMotor = name

    @property
    def nameMotor(self) -> str:
        return self._nameMotor

    @nameMotor.setter
    def nameMotor(self, nameMotor: str):
        self._nameMotor = nameMotor

    @nameMotor.deleter
    def nameMotor(self):
        del self._nameMotor

    @property
    def uebersetzung(self) -> float:
        return self._uebersetzung

    @uebersetzung.setter
    def uebersetzung(self, uebersetzung: float):
        self._uebersetzung = uebersetzung

    @uebersetzung.deleter
    def uebersetzung(self):
        del self._uebersetzung

    @property
    def anschluss(self):
        return self._anschluss

    @anschluss.setter
    def anschluss(self, anschluss: Anschluss):
        self._anschluss = anschluss

    @anschluss.deleter
    def anschluss(self):
        del self._anschluss
