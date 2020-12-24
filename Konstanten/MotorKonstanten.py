import enum


class MotorKonstanten(enum.Enum):
    LINKS = -1
    RECHTS = 1
    VOR = -1
    ZURUECK = 1
    WINKEL = 0x0b
    ZEIT = 0x09
