from abc import ABC

from Geraet.Motor import Motor
from Geraet.MotorTyp.EinzelMotor import EinzelMotor
from Konstanten.Anschluss import Anschluss


class KombinierterMotor(Motor, ABC):
    '''Kombination aus 2 (zwei) verschiedenen Motoren. Kommandos-Ausführung ist synchronisiert.
    '''

    def __init__(self, ersterMotor: EinzelMotor, zweiterMotor: EinzelMotor, uebersetzung: float = 1.0, name: str = ""):
        """

        :param ersterMotor:
        :param zweiterMotor:
        :param name:
        """
        self.ersterMotorPort = ersterMotor.anschluss
        self.zweiterMotorPort = zweiterMotor.anschluss
        self._uebersetzung = uebersetzung

        self._anschluss = None
        self._nameMotor = name

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
