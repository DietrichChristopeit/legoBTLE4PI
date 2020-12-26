from Konstanten.Anschluss import Anschluss
from Motor.Motor import Motor
from Motor.EinzelMotor import EinzelMotor
from Konstanten.SI_Einheit import SI_Einheit
from collections import namedtuple


class KombinierterMotor(Motor):
    '''
    Kombination aus 2 (zwei) verschiedenen Motoren. Kommandos-Ausführung ist synchronisiert.
    '''

    def __init__(self, ersterMotor: EinzelMotor, zweiterMotor: EinzelMotor, name: str = None):
        """

        :param ersterMotor:
        :param zweiterMotor:
        :param name:
        """
        self.ersterMotorPort = ersterMotor.anschlussDesMotors
        self.zweiterMotorPort = zweiterMotor.anschlussDesMotors
        self.name = name

    def konfiguriereGemeinsamenPort(self) -> int:
        """Konfiguriert ersten und zweiten Motor als einen gemeinsamen Motor mit neuem Anschlusss (Port).

            :return: Gibt die Anschlussnummer des gemeinsamen Anschlusses (Port) zurück.
        """
        raise NotImplementedError

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
        raise NotImplementedError
