#  MIT License
#
#  Copyright (c) 2021 Dietrich Christopeit
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import math
from enum import Enum


class SIUnit(Enum):
    """This class defines some important constants that are used to control the motors or to convert units.

    """
    #Für die Ansteuerung der Motoren in ° oder in Millisekunden
    ANGLE = 0x0b
    """Für die Ansteuerung der Motoren in °."""
    TIME = 0x09
    """Für die Ansteuerung der Motoren in Millisekunden."""
    #Für die Umrechnung von Einheiten
    ROUND = 1
    METER = 1
    MILLIMETER = METER.value / 1000
    METER_PER_SEC = METER.value / (1000 * 1)
    RPS = 1 / (1000 * 1)
    DPS = 1 / (1000 * 1)
    DISTANCE2DEGREE = 180 / math.pi
