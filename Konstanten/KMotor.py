from enum import Enum


class KMotor(Enum):
    LINKS: int = -1
    RECHTS: int = 1
    VOR: int = LINKS
    ZURUECK: int = RECHTS
    BREMSEN: int = 0x7f
    FESTHALTEN: int = 0x7e
    AUSLAUFEN: int = 0x00
