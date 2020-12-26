from Konstanten.SI_Einheit import SI_Einheit
from Konstanten.Motor import Motor as MotorKonstanten

class Motor:
    """Interface für alle Motoren. Design noch nicht endgültig."""

    @property
    def nameDesMotors(self):
        raise NotImplementedError

    @property
    def anschlussDesMotors(self):
        raise NotImplementedError

    def dreheMotorFuerT(self, millisekunden: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                        zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> str:
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

        characteristic: str = '0c0081' + '{:02x}'.format(self.anschlussDesMotors.value) + '1109' + millisekunden.to_bytes(2,
                                                                                                                          byteorder='little',
                                                                                                                          signed=False).hex() \
                              + power.to_bytes(1, byteorder='little', signed=True).hex() + '64' + '{:02x}'.format(
                zumschluss.value) + '03'

        return characteristic

    def dreheMotorFuerGrad(self, grad: int, richtung: MotorKonstanten = MotorKonstanten.VOR, power: int = 50,
                           zumschluss: MotorKonstanten = MotorKonstanten.BREMSEN) -> str:
        raise NotImplementedError

    def dreheMotor(self, SI: SI_Einheit, wertDerEinheit: int = 0, richtung: MotorKonstanten = MotorKonstanten.VOR,
                   power: int = 50, zumschluss:
            MotorKonstanten = MotorKonstanten.BREMSEN) -> str:
        raise NotImplementedError
