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

from abc import ABC, abstractmethod

from Konstanten.Anschluss import Anschluss
from Konstanten.KMotor import KMotor
from Konstanten.SI_Einheit import SI_Einheit
from MessageHandling.MessageQueue import MessageQueue
import threading


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

    @property
    @abstractmethod
    def pipeline(self) -> MessageQueue:
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> int:
        raise NotImplementedError

    @status.setter
    @abstractmethod
    def status(self, status) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def vorherigerWinkel(self) -> int:
        raise NotImplementedError

    @vorherigerWinkel.setter
    @abstractmethod
    def vorherigerWinkel(self, value):
        raise NotImplementedError

    @property
    @abstractmethod
    def aktuellerWinkel(self) -> int:
        raise NotImplementedError

    @aktuellerWinkel.setter
    @abstractmethod
    def aktuellerWinkel(self, value):
        raise NotImplementedError

    @abstractmethod
    def start(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def listenMessageQueue(self, pipeline: MessageQueue, event):
        raise NotImplementedError

    def dreheMotorFuerT(self, millisekunden: int, richtung: int = KMotor.VOR, power: int = 50,
                        zumschluss: int = KMotor.BREMSEN) -> bytes:
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
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotorFuerGrad(self, grad: int, richtung: int = KMotor.VOR, power: int = 50,
                           zumschluss: int = KMotor.BREMSEN) -> bytes:
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
                port = '{:02x}'.format(self.anschluss.value)
            else:
                port = self.anschluss
            befehl: str = '0e0081{}110b'.format(port) + grad.to_bytes(4,
                                                                      byteorder='little',
                                                                      signed=False).hex() \
                          + power.to_bytes(1, byteorder='little', signed=True).hex() + '64{:02x}03'.format(
                zumschluss.value)
        except AssertionError:
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')

        return bytes.fromhex(befehl)

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: int = 0, richtung: int = KMotor.VOR,
                   power: int = 50, zumschluss: int = KMotor.BREMSEN) -> bytes:
        """Diese Methode dreht einen Motor, wobei der Aufrufer die Art durch die Angabe der Einheit spezifiziert.


        :rtype: 
            str
        :param SI: 
            SI-Einheit basierend auf welcher der Motor gedreht werden soll (z.B. SI_Einheit.WINKEL).
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

        befehl: str = ''
        return bytes.fromhex(befehl)

    def processMessage(self, message):
        if message[2] == 0x45:
            self.vorherigerWinkel = self.aktuellerWinkel
            self.aktuellerWinkel = int(''.join('{:02x}'.format(m) for m in message[4:7][::-1]), 16)
        if message[2] == 0x82:
            self.status = message[4]

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
            print('Motor ist keinem Anschluss zugewiesen... Programmende...')
        return bytes.fromhex(befehl)


class EinzelMotor(Motor, ABC):

    def __init__(self, port: Anschluss, event: threading.Event, uebersetzung: float = 1.0, name: str = None):
        """Die Klasse EinzelMotor dient der Erstellung eines einzelnen neuen Motors.


        :type port: Anschluss
        :param port:
            Ein Anschluss, z.B. Anschluss.A .
        :param uebersetzung:
            Das Verhältnis von treibendem Zahnrad zu angetriebenem Zahnrad, Standard = 1.0 (keine Übersetzung)
        :param name:
            Eine gute Bezeichnung, die beschreibt, was der Motor tun soll.
        """

        self._status = 0x0a
        self._pipeline = MessageQueue()
        self._anschluss = port
        self._id = port
        self._event = event
        self._nameMotor = name
        self._uebersetzung = uebersetzung
        self._notif_thr = threading.Thread(target=self.listenMessageQueue,
                                           args={self._pipeline, self._event})  # Event Loop als neuer Thread
        self._aktuellerWinkel = 0
        self._vorherigerWinkel = 0
        self._upm = 0x00

    def start(self) -> bool:
        if self._notif_thr is not None:
            self._notif_thr.start()
            return True
        else:
            return False

    def listenMessageQueue(self, pipeline: MessageQueue, event):
        """Mit dieser Methode werden die Notifications behandelt.

        :param pipeline:
            Dieser Parameter stellt die Verbindung zum Hub dar. Jeder KMotor hat eine eigene Pipeline.
        :param event:
            Dieser Parameterist das Ereignis, welches gesetzt wird, wenn die Verarbeitung beendet ist.
        :return:
        """
        while not event.is_set():
            message = bytes.fromhex(pipeline.get_message(id(self)))
            if message[3] == self._anschluss:
                self.processMessage(message)
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                continue
            print('.', end='')

        while not pipeline.qsize() == 0:  # process remaining items in queue
            message = bytes.fromhex(pipeline.get_message(self.id))
            if message[3] == self._anschluss:
                self.processMessage(message)
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                continue
        print('[MOTOR]-[MSG]: mQueue shutting down... exiting...')
        self._notif_thr.join(2)

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def vorherigerWinkel(self) -> int:
        return self._vorherigerWinkel

    @vorherigerWinkel.setter
    def vorherigerWinkel(self, winkel):
        self._vorherigerWinkel = winkel

    @property
    def aktuellerWinkel(self) -> int:
        return self._aktuellerWinkel

    @aktuellerWinkel.setter
    def aktuellerWinkel(self, winkel):
        self._aktuellerWinkel = winkel

    @property
    def id(self) -> Anschluss:
        return self._id

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

    @property
    def pipeline(self) -> MessageQueue:
        return self._pipeline

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
    '''Kombination aus 2 (zwei) verschiedenen Motoren. Kommandos-Ausführung ist synchronisiert.
    '''

    def __init__(self, ersterMotor: EinzelMotor, zweiterMotor: EinzelMotor, uebersetzung: float = 1.0, name: str = ""):
        """

        :param ersterMotor:
        :param zweiterMotor:
        :param name:
        """
        self._status = 0x00
        self._pipeline = MessageQueue()
        self._ersterMotorPort = ersterMotor.anschluss
        self._zweiterMotorPort = zweiterMotor.anschluss
        self._uebersetzung = uebersetzung

        self._anschluss = f"{ersterMotor.anschluss:02}{zweiterMotor.anschluss:02}"
        self._nameMotor = name

    @property
    def vorherigerWinkel(self) -> int:
        return self._vorherigerWinkel

    @vorherigerWinkel.setter
    def vorherigerWinkel(self, winkel):
        self._vorherigerWinkel = winkel

    @property
    def aktuellerWinkel(self) -> int:
        return self._aktuellerWinkel

    @aktuellerWinkel.setter
    def aktuellerWinkel(self, winkel):
        self._aktuellerWinkel = winkel

    @property
    def status(self) -> int:
        return self._status

    def start(self) -> bool:
        if self._notif_thr is not None:
            self._notif_thr.start()
            return True
        else:
            return False

    @property
    def pipeline(self) -> MessageQueue:
        return self._pipeline

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

    @property
    def ersterMotorPort(self) -> Anschluss:
        return self._ersterMotorPort

    @property
    def zweiterMotorPort(self) -> Anschluss:
        return self._zweiterMotorPort

    @anschluss.deleter
    def anschluss(self):
        del self._anschluss

    def listenMessageQueue(self, pipeline: MessageQueue, event):
        """Mit dieser Methode werden die Notifications behandelt.

                :param pipeline:
                    Dieser Parameter stellt die Verbindung zum Hub dar. Jeder Motor hat eine eigene Pipeline.
                :param event:
                    Dieser Parameterist das Ereignis, welches gesetzt wird, wenn die Verarbeitung beendet ist.
                :return:
                """
        while not event.is_set():
            message = bytes.fromhex(pipeline.get_message(id(self)))
            if message[3] == self._anschluss:
                self.processMessage(message)
                print("[VMOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3], message))
                continue
            elif (message[len(message)-1] == self._zweiterMotorPort) and (message[len(message)-2] == self._zweiterMotorPort):
                print(f"[VMOTOR]-[RCV]: Es wird Anschluss {message[3]:02x} den kombinierten Motor gesetzt")
                self._anschluss = message[3]
                continue
            print('.', end='')

        while not pipeline.qsize() == 0:  # process remaining items in queue
            message = bytes.fromhex(pipeline.get_message(self.id))
            if message[3] == self._anschluss:
                self.processMessage(message)
                print("[MOTOR]-[RCV]: Habe für Anschluss {:02x} die Nachricht {:02x} erhalten".format(message[3],
                                                                                                      message))
                continue
        print('[MOTOR]-[MSG]: mQueue shutting down... exiting...')
        self._notif_thr.join(2)
