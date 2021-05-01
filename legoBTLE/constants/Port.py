"""
    legoBTLE.constants.Port
    ~~~~~~~~~~~~~~~~~~~~~~~

    Some enums  for often used port constant values.
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
"""

from enum import Enum


class Port(Enum):
    A = b'\x00'
    B = b'\x01'
    C = b'\x02'


PORT = {
        b'\x00': Port.A,
        b'\x01': Port.B,
        b'\x02': Port.C
        }
