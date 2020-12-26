from Konstanten.Anschluss import Anschluss
from Motor.Motor import Motor
from Motor.EinzelMotor import EinzelMotor
from Konstanten.SI_Einheit import SI_Einheit
from collections import namedtuple


class KombinierterMotor(Motor):
    '''
    Kombination aus verschiedenen Motoren und Kommandos, Ausführung synchronisiert.
    '''

    def __init__(self, port: Anschluss, motoren: EinzelMotor = [], name: str = None):
        """Lorem ipsum

        :param port:
        :param motoren:
        :param name:
        """
        self.port = port
        for motor in range(len(motoren)):
            self.motoren.append(motor)
        self.name = name

    @property
    def nameDesMotors(self):
        return self.nameDesMotors

    @property
    def anschlussDesMotors(self):
        return self.port

    def weiseKommandosZu(self, kommandos: ['SI, SIWert, Richtung, KraftInProzent, SchlussAktion']) -> []:
        '''Lorem ipsum

        :param kommandos:
        :return:
        '''
        i = 0
        hexcommands = []
        for kommando in kommandos:
            if kommando[0] == SI_Einheit.ZEIT:
                hexcommands[i] = EinzelMotor(self.motoren[i]).dreheMotorFuerT(kommando[1], kommando[2], kommando[3], kommando[4])
            else:
                hexcommands[i] = EinzelMotor(self.motoren[i]).dreheMotorFuerGrad(kommando[1], kommando[2], kommando[3],
                                                                                 kommando[4])
            i += 1

        return hexcommands

    def fuehreKommandosAus(self):
        pass
