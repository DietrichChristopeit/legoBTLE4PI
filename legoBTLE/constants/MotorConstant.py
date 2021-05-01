"""
    legoBTLE.constants.MotorConstant
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements some often needed constant values for :class:`legoBTLE.device.AMotor.AMotor`.
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
"""

from enum import Enum


class MotorConstant(Enum):
    """:class:`MotorConstant`
    
    Enum for some constants.
    
    """
    LEFT: bytes = b'\xff'
    RIGHT: bytes = b'\x01'
    FORWARD: bytes = LEFT
    BACKWARD: bytes = RIGHT
    BREAK: bytes = b'\x7f'
    HOLD: bytes = b'\x7e'
    COAST: bytes = b'\x00'
    RUNNING: bytes = b'\x00'
    FINISHED: bytes = b'\x0a'


M_Constants = {b'\xff': {MotorConstant.LEFT, MotorConstant.FORWARD},
               b'\x01': {MotorConstant.RIGHT, MotorConstant.BACKWARD},
               b'\x7f': MotorConstant.BREAK,
               b'\x7e': MotorConstant.HOLD,
               b'\x00': {MotorConstant.COAST, MotorConstant.RUNNING},
               b'\x0a': MotorConstant.FINISHED
               }
