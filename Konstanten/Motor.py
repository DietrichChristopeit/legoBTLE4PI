from enum import Enum


class Motor(Enum):
    LINKS: int = -1
    RECHTS: int = 1
    VOR: int = -1
    ZURUECK: int = 1
    BREMSEN: int = 0x7f
    FESTHALTEN: int = 0x7e
    AUSLAUFEN: int = 0x00
