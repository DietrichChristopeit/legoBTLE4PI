from MotorTyp.EinzelMotor import EinzelMotor
from Konstanten.SI_Einheit import SI_Einheit
from collections import namedtuple


class KombinierterMotor:
    '''
    Kombination aus verschiedenen Motoren und Kommandos, Ausführung synchronisiert.
    '''

    def __init__(self, motoren: EinzelMotor = []):
        '''

        :param motoren:
        '''
        for motor in range(len(motoren)):
            self.motoren.append(motor)

    def weiseKommandosZu(self, kommandos: ['SI, SIWert, Richtung, KraftInProzent, SchlussAktion']):
        '''

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

    def fuehreKommandosAus(self):
        pass
