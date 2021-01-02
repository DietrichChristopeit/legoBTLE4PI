import sys
from abc import ABC, abstractmethod

from Konstanten.Anschluss import Anschluss
from Konstanten.SI_Einheit import SI_Einheit
from Konstanten.Motor import Motor as MotorKonstanten


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
                MotorKonstanten.BREMSEN = der MotorTyp wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
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
                                                                                                                  byteorder='little', signed=False).hex())
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
