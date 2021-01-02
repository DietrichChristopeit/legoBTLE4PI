from abc import ABC, abstractmethod

from Geraet.Motor import Motor


class Controller(ABC, abstractmethod):

    @abstractmethod
    def initialisiereController(self, kennzeichen) -> bool:
        raise NotImplementedError

    @abstractmethod
    def konfiguriereAnschlussFuer(self, motor: Motor) -> bool:
        raise NotImplementedError
