import math
from enum import Enum


class SI_Einheit(Enum):
    """Diese Klasse definiert einige wichtige Konstanten, die zur Steuerung der Motoren, bzw. für die Umrechnung von Einheiten
    notwendig sind.

    """
    #Für die Ansteuerung der Motoren in ° oder in Millisekunden
    WINKEL = 0x0b
    """Für die Ansteuerung der Motoren in °."""
    ZEIT = 0x09
    """Für die Ansteuerung der Motoren in Millisekunden."""
    #Für die Umrechnung von Einheiten
    UMDREHUNG = 1
    METER = 1
    MILLIMETER = METER / 1000
    METER_PRO_SEK = METER / (1000 * 1)
    RPS = 1 / (1000 * 1)
    DPS = 1 / (1000 * 1)
    STRECKE2GRAD = 180 / math.pi
