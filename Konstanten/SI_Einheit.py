from enum import Enum


class SI_Einheit(Enum):
    WINKEL = 0x0b
    UMDREHUNG = 1
    ZEIT = 0x09
    METER = 1
    MILLIMETER = METER // 1000
    METER_PRO_SEK = METER // (1000 * 1)
    RPS = 1 // (1000 * 1)
    DPS = 1 // (1000 * 1)
