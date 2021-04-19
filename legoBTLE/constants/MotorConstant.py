"""
legoBTLE.constants.MotorConstant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The module implements some often needed constant values for :class:`legoBTLE.device.AMotor`.

"""
# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************

from enum import Enum


class MotorConstant(Enum):
    """
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
