from enum import Enum


class Motor(Enum):
    LINKS = -1
    RECHTS = 1
    VOR = -1
    ZURUECK = 1
    WINKEL = 0x0b
    ZEIT = 0x09
    BREMSEN = 0x7f
    FESTHALTEN = 0x7e
    AUSLAUFEN = 0x00
