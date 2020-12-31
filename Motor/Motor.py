import sys
from abc import ABC, abstractmethod

from Konstanten.Anschluss import Anschluss
from Konstanten.SI_Einheit import SI_Einheit
from Konstanten.Motor import Motor as MotorKonstanten


class Motor(ABC):
    """Abstrakte Basisklasse für alle Motoren. Design noch nicht endgültig."""

    @property
    @abstractmethod
    def nameDesMotors(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def anschlussDesMotors(self):
        raise NotImplementedError

    def dreheMotorFuerT(self, millisekunden: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                        zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Zeit berechnen lassen.

            :rtype:
                str
            :param millisekunden:
                Die Dauer, für die der Motor sich drehen soll.
            :param richtung:
                Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
                MotorKonstanten.LINKS oder
                MotorKonstanten.RECHTS).
            :param power:
                Ein Wert von 0 bis 100.
            :param zumschluss:
                Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
                d.h. MotorKonstanten.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
                Stillstand;
                MotorKonstanten.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
                MotorKonstanten.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
                den Motor zu
                drehen.
            :returns:
                Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power
        zs = zumschluss.value
        befehl: str = ''

        try:
            assert self.anschlussDesMotors is not None
            if isinstance(self.anschlussDesMotors, Anschluss):
                port = '{:02x}'.format(self.anschlussDesMotors.value)
            else:
                port = self.anschlussDesMotors

            befehl: str = '0c0081{}1109'.format(port) + millisekunden.to_bytes(2, byteorder='little',
                                                                                                            signed=False).hex() \
                          + \
                          power.to_bytes(1, byteorder='little', signed=True).hex() + '64{}03'.format(zs.to_bytes(1,
                                                                                                                  byteorder='little', signed=False).hex())
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotorFuerGrad(self, grad: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                           zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Anzahl Grad (°) berechnen lassen.


        :param grad:
            Der Winkel in ° um den der Motor, d.h. dessen Welle gedreht werden soll. Ein ganzzahliger Wert, z.B. 10,
            12, 99 etc.
        :param richtung:
            Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
            MotorKonstanten.LINKS oder
            MotorKonstanten.RECHTS).
        :param power:
            Ein Wert von 0 bis 100.
        :param zumschluss:
            Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. MotorKonstanten.AUSLAUFEN = der Motor hält nicht sofort an sodern dreht sich aus eigener Kraft bis zum
            Stillstand;
            MotorKonstanten.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
            MotorKonstanten.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den Motor zu drehen.
        :rtype:
            str
        :returns:
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power

        befehl: str = ''

        try:
            assert self.anschlussDesMotors is not None
            if isinstance(self.anschlussDesMotors, Anschluss):
                port = '{:02x}'.format(self.anschlussDesMotors.value)
            else:
                port = self.anschlussDesMotors
            befehl: str = '0e0081{}110b'.format(port) + grad.to_bytes(4,
                                                                                                   byteorder='little',
                                                                                                   signed=False).hex() \
                          + power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(zumschluss.value)
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: int = 0, richtung: MotorKonstanten = MotorKonstanten.VOR,
                   power: int = 50, zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> str:
        """Diese Methode dreht einen Motor, wobei der Aufrufer die Art durch die Angabe der Einheit spezifiziert.


        :rtype: 
            str
        :param SI: 
            SI-Einheit basierend auf welcher der Motor gedreht werden soll (z.B. SI_Einheit.WINKEL).
        :param wertDerEinheit: 
            Um welchen Wert in der Einheit SI soll gedreht werden.
        :param richtung: 
            Entweder die Fahrrichtung (MotorKonstanten.VOR oder MotorKonstanten.ZURUECK) oder die Lenkrichtung (
            MotorKonstanten.LINKS oder
            MotorKonstanten.RECHTS).
        :param power: 
            Ein Wert von 0 bis 100.
        :param zumschluss: 
            Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll, 
            d.h. 
            * MotorKonstanten.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum 
            Stillstand; 
            * MotorKonstanten.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht 
            werden; 
            * MotorKonstanten.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen, 
            den Motor zu drehen.
        :returns: 
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        befehl: str = ''
        return bytes.fromhex(befehl)

    def resetMotor(self):
        try:
            assert self.anschlussDesMotors is not None
            if isinstance(self.anschlussDesMotors, Anschluss):
                port = '{:02x}'.format(self.anschlussDesMotors.value)
            else:
                port = self.anschlussDesMotors
            befehl: str = '0b0081{}11510200000000'.format(port)
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')
        return bytes.fromhex(befehl)
