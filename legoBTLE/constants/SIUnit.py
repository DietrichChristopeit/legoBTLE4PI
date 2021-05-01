"""
    legoBTLE.constants.SIUnit
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Module modeling SI Units.
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
"""

import math
from enum import Enum


class SIUnit(Enum):
    """:class:`legoBTLE.constants.SIUnit.SIUnit`
    
    This class defines some important constants that are used to control the motors or to convert units.

    """
    # Für die Ansteuerung der Motoren in ° oder in Millisekunden
    ANGLE = 0x0b
    """Für die Ansteuerung der Motoren in °."""
    TIME = 0x09
    """Für die Ansteuerung der Motoren in Millisekunden."""
    # Für die Umrechnung von Einheiten
    ROUND = 1
    METER = 1
    MILLIMETER = METER / 1000
    METER_PER_SEC = METER / (1000 * 1)
    RPS = 1 / (1000 * 1)
    DPS = 1 / (1000 * 1)
    DISTANCE2DEGREE = 180 / math.pi
