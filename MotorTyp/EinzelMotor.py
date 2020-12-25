from Konstanten.SI_Einheit import SI_Einheit
from Konstanten.Motor import Motor
from Konstanten.Anschluss import Anschluss


class EinzelMotor:

    def __init__(self, port: Anschluss, name: str = None):
        '''
        Die Klasse EinzelMotor dient der Erstellung eines einzelnen neuen Motors.

        :param port: Ein Anschluss, z.B. Anschluss.A .
        :param name: Eine gute Bezeichnung, die beschreibt, was der Motor tun soll.
        '''

        self.port = port
        self.name = name

    @property
    def nameDesMotors(self):
        return self.nameDesMotors

    @property
    def anschlussDesMotors(self):
        return self.port

    def dreheMotorFuerT(self, millisekunden: int, richtung: Motor = Motor.VOR, power: int = 50,
                        zumschluss: Motor = Motor.BREMSEN) -> str:
        """
        Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Zeit berechnen lassen.

        :rtype: str
        :param millisekunden: Die Dauer, für die der Motor sich drehen soll.
        :param richtung: Entweder die Fahrrichtung (Motor.VOR oder Motor.ZURUECK) oder die Lenkrichtung (Motor.LINKS oder
        Motor.RECHTS).
        :param power: Ein Wert von 0 bis 100.
        :param zumschluss: Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
        d.h. Motor.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum Stillstand;
        Motor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
        Motor.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen, den Motor zu drehen.
        :returns: Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power

        characteristic: str = '0c0081' + '{:02x}'.format(self.anschlussDesMotors.value) + '1109' + millisekunden.to_bytes(2,
                                                                                                                      byteorder='little',
                                                                                                                     signed=False).hex() \
                         + power.to_bytes(1, byteorder='little', signed=True).hex() + '64' + '{:02x}'.format(zumschluss.value) + '03'

        return characteristic

    def dreheMotorFuerGrad(self, grad: int, richtung: Motor=Motor.VOR, power: int=50, zumschluss: Motor=Motor.BREMSEN) -> str:
        """
        Mit dieser Methode kann man das Kommando zum Drehen eines Motors für eine bestimmte Zeit berechnen lassen.

        :param grad: Der Winkel in ° um den der Motor, d.h. dessen Welle gedreht werden soll. Ein ganzzahliger Wert, z.B. 10,
        12, 99 etc.
        :param richtung: Entweder die Fahrrichtung (Motor.VOR oder Motor.ZURUECK) oder die Lenkrichtung (Motor.LINKS oder
        Motor.RECHTS).
        :param power: Ein Wert von 0 bis 100.
        :param zumschluss: Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll,
        d.h. Motor.AUSLAUFEN = der Motor hält nicht sofort an sodern dreht sich aus eigener Kraft bis zum Stillstand;
        Motor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden;
        Motor.FESTHALTEN = Motor wird in der Endposition gehalten, auch wenn Kräfte von aussen versuchen, den Motor zu drehen.
        :rtype: str
        :returns: Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        """

        power = richtung.value * power

        characteristic: str = '0e0081' + '{:02x}'.format(self.anschlussDesMotors.value) + '110b' + grad.to_bytes(4,
                                                                                                                 byteorder='little', signed=False).hex() \
                         + power.to_bytes(1, byteorder='little', signed=True).hex() + '64' + '{:02x}'.format(zumschluss.value) + '03'
        return characteristic

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: int=0, richtung: Motor=Motor.VOR, power: int=50, zumschluss:
    Motor=Motor.BREMSEN ) -> str:
        '''
        
        :rtype: str
        :param SI: SI-Einheit basierend auf welcher der Motor gedreht werden soll (z.B. SI_Einheit.WINKEL).
        :param wertDerEinheit: Um welchen Wert in der Einheit SI soll gedreht werden.
        :param richtung: Entweder die Fahrrichtung (Motor.VOR oder Motor.ZURUECK) oder die Lenkrichtung (Motor.LINKS oder
        Motor.RECHTS).
        :param power: Ein Wert von 0 bis 100.
        :param zumschluss: Bestimmt, wie sich der Motor, nachdem die Drehungen beendet wurden, verhalten soll, 
        d.h. Motor.AUSLAUFEN = der Motor hält nicht sofort an, sodern dreht sich aus eigener Kraft bis zum Stillstand; 
        Motor.BREMSEN = der Motor wird angehalten, kann jedoch durch Krafteinwirkung von aussen gedreht werden; Motor.FESTHALTEN = Motor wird in der
        Endposition gehalten, auch wenn Kräfte von aussen versuchen, den Motor zu drehen.
        :returns: Das aus den Angaben berechnete Kommando wird zurückgeliefert.
        '''

        characteristic: str = ''
        return characteristic

    def setzeZählwerkAufNull(self, SI: SI_Einheit):
        '''
        Mit dieser Methode wir der Zähler für die SI-Einheit SI (z.B. SI_Einheit.WINKEL) auf 0 gesetzt.
        Falls eine falsche Einheit gewählt wird, wird eine Fehlermeldung ausgegeben und das Programm beendet.

        :param SI: SI-Einheit des Zählers (z.B. SI_Einheit.WINKEL).
        :return: Es wird kein Ergebnis zurückgegeben.
        '''
        if SI == SI_Einheit.WINKEL:
            pass #setzte Gradzähler auf 0
        elif SI == SI_Einheit.UMDREHUNG:
            pass #setze Umdrehungszähler auf 0
        else:
            raise Exception("Der Zähler für die Einheit" + SI +" kann nicht zurückgesetzt werden. Falsche Einheit.").with_traceback()


    def kalibriereMotor(self) -> float:
        '''
        Mit dieser Methode wird ein Motor sozusagen in die Mitte gestellt.

        :return: Der maximale Winkel, den der Motor in eine Richtung drehen kann.
        '''

        maxWinkel = 0
        return maxWinkel
