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
import threading
from abc import ABC, abstractmethod

from Konstanten.Anschluss import Anschluss
from Konstanten.KMotor import KMotor
from Konstanten.SI_Einheit import SI_Einheit


class Motor(ABC):
    """Abstrakte Basisklasse für alle Motoren. Design noch nicht endgültig."""

    @property
    @abstractmethod
    def upm(self) -> int:
        raise NotImplementedError

    @upm.setter
    @abstractmethod
    def upm(self, upm):
        raise NotImplementedError

    @upm.deleter
    @abstractmethod
    def upm(self):
        raise NotImplementedError

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

    @property
    @abstractmethod
    def vorherigerWinkel(self) -> float:
        raise NotImplementedError

    @vorherigerWinkel.setter
    @abstractmethod
    def vorherigerWinkel(self, value: float):
        raise NotImplementedError

    @property
    @abstractmethod
    def aktuellerWinkel(self) -> float:
        raise NotImplementedError

    @aktuellerWinkel.setter
    @abstractmethod
    def aktuellerWinkel(self, value: float):
        raise NotImplementedError

    @property
    @abstractmethod
    def waitCmd(self) -> threading.Event:
        raise NotImplementedError

    def dreheMotorFuerT(self, millisekunden: int, richtung: KMotor = KMotor.VOR, power: int = 50,
                        zumschluss: KMotor = KMotor.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Zeit berechnen lassen.

            :rtype:
                str
            :param millisekunden:
                Die Dauer, für die der MotorTyp sich drehen soll.
            :param richtung:
                Entweder die Fahrrichtung (KMotor.VOR oder KMotor.ZURUECK) oder die Lenkrichtung (
                KMotor.LINKS oder
                KMotor.RECHTS).
            :param power:
                Ein Wert von 0 bis 100.
            :param zumschluss:
                Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
                d.h. KMotor.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
                Stillstand;
                KMotor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht
                werden;
                KMotor.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
                den Motor zu
                drehen.
            :returns:
                Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power
        befehl: str = ''

        try:
            assert self.anschluss is not None
            if isinstance(self.anschluss, Anschluss):
                port = self.anschluss.value
            else:
                port = self.anschluss

            befehl: str = '0c0081{:02x}1109'.format(port) + millisekunden.to_bytes(2, byteorder='little',
                                                                               signed=False).hex() \
                          + \
                          power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(zumschluss.value)
            print(befehl)
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotorFuerGrad(self, grad: float, richtung: KMotor = KMotor.VOR, power: int = 50,
                           zumschluss: KMotor = KMotor.BREMSEN) -> bytes:
        """Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Anzahl Grad (°) berechnen lassen.


        :param grad:
            Der Winkel in ° um den der MotorTyp, d.h. dessen Welle gedreht werden soll. Ein ganzzahliger Wert, z.B. 10,
            12, 99 etc.
        :param richtung:
            Entweder die Fahrrichtung (KMotor.VOR oder KMotor.ZURUECK) oder die Lenkrichtung (
            KMotor.LINKS oder
            KMotor.RECHTS).
        :param power:
            Ein Wert von 0 bis 100.
        :param zumschluss:
            Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. KMotor.AUSLAUFEN = der Motor hält nicht sofort an sodern dreht sich aus eigener Kraft bis zum
            Stillstand;
            KMotor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
            KMotor.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den Motor zu drehen.
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
                port = self.anschluss.value
            else:
                port = self.anschluss
            befehl: str = '0e0081{:02x}110b'.format(port) + grad.to_bytes(4,
                                                                      byteorder='little',
                                                                      signed=False).hex() \
                          + power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(
                    zumschluss.value)
        except AssertionError:
            print('Motor {} ist keinem Anschluss zugewiesen... Programmende...'.format(self.nameMotor))

        return bytes.fromhex(befehl)

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: float = 0.0, richtung: KMotor = KMotor.VOR,
                   power: int = 50, zumschluss: KMotor = KMotor.BREMSEN) -> bytes:
        """Diese Methode dreht einen Motor, wobei der Aufrufer die Art durch die Angabe der Einheit spezifiziert.


        :rtype: 
            str
        :param SI: 
            SI-Einheit, basierend auf welcher der Motor gedreht werden soll (z.B. SI_Einheit.WINKEL).
        :param wertDerEinheit: 
            Um welchen Wert in der Einheit SI soll gedreht werden.
        :param richtung: 
            Entweder die Fahrrichtung (KMotor.VOR oder KMotor.ZURUECK) oder die Lenkrichtung (
            KMotor.LINKS oder
            KMotor.RECHTS).
        :param power: 
            Ein Wert von 0 bis 100.
        :param zumschluss: 
            Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
            d.h. 
            * KMotor.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum
            Stillstand; 
            * KMotor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht
            werden; 
            * KMotor.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen,
            den Motor zu drehen.
        :returns: 
            Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """
        befehl: bytes = b'\x00'

        if SI == SI.WINKEL:
            befehl = self.dreheMotorFuerGrad(wertDerEinheit, richtung, power, zumschluss)
        elif SI == SI.ZEIT:
            befehl = self.dreheMotorFuerT(int(wertDerEinheit), richtung, power, zumschluss)

        return befehl

    def reset(self) -> bytes:
        befehl: str = ''
        try:
            assert self.anschluss is not None
            if isinstance(self.anschluss, Anschluss):
                port = self.anschluss.value
            else:
                port = self.anschluss
            befehl: str = '0b0081{:02x}11510200000000'.format(port)
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')
        return bytes.fromhex(befehl)


class EinzelMotor(threading.Thread, Motor):

    def __init__(self, motorAnschluss: Anschluss, uebersetzung: float = 1.0, name: str = None):
        """Die Klasse EinzelMotor dient der Erstellung eines einzelnen neuen Motors.


        :type motorAnschluss: Anschluss
        :param motorAnschluss:
            Ein Anschluss, z.B. Anschluss.A .
        :param uebersetzung:
            Das Verhältnis von treibendem Zahnrad zu angetriebenem Zahnrad, Standard = 1.0 (keine Übersetzung)
        :param name:
            Eine gute Bezeichnung, die beschreibt, was der Motor tun soll.
        """
        super().__init__()
        self._waitCmd = threading.Event()
        self._waitCmd.clear()
        self._anschluss = motorAnschluss
        self._nameMotor: str = name
        self._uebersetzung: float = uebersetzung
        self._aktuellerWinkel: float = 0.00
        self._vorherigerWinkel: float = 0.00
        self._upm: int = 0

    def run(self):

    @property
    def waitCmd(self) -> threading.Event:
        return self._waitCmd

    @property
    def upm(self) -> int:
        return self._upm

    @upm.setter
    def upm(self, upm: int):
        self._upm = upm

    @upm.deleter
    def upm(self):
        del self._upm

    @property
    def vorherigerWinkel(self) -> float:
        return self._vorherigerWinkel

    @vorherigerWinkel.setter
    def vorherigerWinkel(self, winkel: float):
        self._vorherigerWinkel = winkel

    @property
    def aktuellerWinkel(self) -> float:
        return self._aktuellerWinkel

    @aktuellerWinkel.setter
    def aktuellerWinkel(self, winkel: float):
        self._aktuellerWinkel = winkel

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
    def anschluss(self) -> Anschluss:
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

        if SI == SI_Einheit.WINKEL:
            pass  # setzte Gradzähler auf 0
        elif SI == SI_Einheit.UMDREHUNG:
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


class KombinierterMotor(Motor):
    """Kombination aus 2 (zwei) verschiedenen Motoren. Kommandos-Ausführung ist synchronisiert.
    """

    def __init__(self, gemeinsamerMotorAnschluss: int,
                 ersterMotorAnschluss: Anschluss, zweiterMotorAnschluss: Anschluss, uebersetzung: float = 1.0,
                 name: str = None):
        """

        :param gemeinsamerMotorAnschluss:
        :param ersterMotorAnschluss:
        :param zweiterMotorAnschluss:
        """

        self._anschluss = gemeinsamerMotorAnschluss  # f"{ersterMotor.anschluss:02}{zweiterMotor.anschluss:02}"
        self._ersterMotorAnschluss = ersterMotorAnschluss
        self._zweiterMotorAnschluss = zweiterMotorAnschluss
        self._uebersetzung: float = uebersetzung

        self._nameMotor: str = name
        self._vorherigerWinkel: float = 0.00
        self._aktuellerWinkel: float = 0.00
        self._waitCmd = threading.Event()
        self._waitCmd.clear()
        self._upm: int = 0

    @property
    def waitCmd(self) -> threading.Event:
        return self._waitCmd

    @property
    def upm(self) -> int:
        return self._upm

    @upm.setter
    def upm(self, upm: int):
        self._upm = upm

    @upm.deleter
    def upm(self):
        del self._upm

    @property
    def vorherigerWinkel(self) -> float:
        return self._vorherigerWinkel

    @vorherigerWinkel.setter
    def vorherigerWinkel(self, winkel: float):
        self._vorherigerWinkel = winkel

    @property
    def aktuellerWinkel(self) -> float:
        return self._aktuellerWinkel

    @aktuellerWinkel.setter
    def aktuellerWinkel(self, winkel: float):
        self._aktuellerWinkel = winkel

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
    def anschluss(self) -> int:
        return self._anschluss

    @anschluss.setter
    def anschluss(self, anschluss: int):
        self._anschluss = anschluss

    @anschluss.deleter
    def anschluss(self):
        del self._anschluss

    @property
    def ersterMotorAnschluss(self) -> Anschluss:
        return self._ersterMotorAnschluss

    @property
    def zweiterMotorAnschluss(self) -> Anschluss:
        return self._zweiterMotorAnschluss

    def definiereGemeinsamenMotor(self):
        return bytes.fromhex(
                '06006101' + '{:02x}'.format(self._ersterMotorAnschluss) + '{:02x}'.format(self._zweiterMotorAnschluss))
