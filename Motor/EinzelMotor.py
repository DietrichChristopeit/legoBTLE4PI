from abc import ABC

from Konstanten.SI_Einheit import SI_Einheit
from Konstanten.Anschluss import Anschluss
from Motor.Motor import Motor


class EinzelMotor(Motor, ABC):

    def __init__(self, port: Anschluss, name: str = None):
        """Die Klasse EinzelMotor dient der Erstellung eines einzelnen neuen Motors.


        :param port:
            Ein Anschluss, z.B. Anschluss.A .
        :param name:
            Eine gute Bezeichnung, die beschreibt, was der Motor tun soll.
        """

        self.port = port
        self.name = name

    @property
    def nameDesMotors(self):
        return self.name

    @property
    def anschlussDesMotors(self):
        return self.port


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
                    "Der Zähler für die Einheit" + SI + " kann nicht zurückgesetzt werden. Falsche Einheit.").with_traceback()


    def kalibriereMotor(self) -> float:
        """Mit dieser Methode wird der Motor sozusagen in die Mitte gestellt.

        :rtype:
            float
        :return:
            Der maximale Winkel, den der Motor in eine Richtung drehen kann.
        """

        maxWinkel = 0
        return maxWinkel
