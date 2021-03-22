# coding=utf-8
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
from abc import abstractmethod
from typing import Tuple, Union

from LegoBTLE.Device.ADevice import Device


class AMotor(Device):

    def port_value_EFF(self):
        return self.port_value.get_port_value_EFF(gearRatio=1.0)

    @property
    @abstractmethod
    def gearRatio(self) -> [float, float]:
        """
        
        :return: The gear ratios.
        :rtype: tuple[float, float]
        """
        raise NotImplementedError

    @gearRatio.setter
    @abstractmethod
    def gearRatio(self, gearRatio_motor_a: float = 1.0, gearRatio_motor_b: float = 1.0) -> None:
        """Sets the gear ratio(s) for the motor(s)
        
        :param float gearRatio_motor_a:
        :param float gearRatio_motor_b:
        :return:
        """
        raise NotImplementedError
    
    @abstractmethod
    async def SET_ACC_PROFILE(self, p_id: int, ):
        """Define a Acceleration Profile and assign it an id.
        
        This method defines an Acceleration Profile and assigns an id.
        It saves or updates the list of Acceleration Profiles and can be set used the Motor Commands
        :func:`GOTO_ABS_POS`, :func:`START_MOVE_DEGREES`
        
        Args:
            p_id (int): The Profile ID

        Returns:

        """
        raise NotImplementedError
    
    @abstractmethod
    async def SET_DECC_PROFILE(self, p_id: int, ):
        raise NotImplementedError
    
    @abstractmethod
    async def START_POWER_UNREGULATED(self, *args):
        raise NotImplementedError
    
    @abstractmethod
    async def GOTO_ABS_POS(self, *args):
        """Sends the command to turn the motor to an absolute position.
        
        See https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-gotoabsoluteposition-abspos-speed-maxpower-endstate-useprofile-0x0d
        
        :param args: The various arguments used to generate this Command.
        
        """
        raise NotImplementedError

    @abstractmethod
    async def START_SPEED(self, *args):
        """Turn the Motor unlimited at a certain speed.
        
        See
            * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed-maxpower-useprofile-0x07
            * https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#output-sub-command-startspeed-speed1-speed2-maxpower-useprofile-0x08
        
        :param args: The various arguments used to generate this Command.
        
        """
        raise NotImplementedError

    @abstractmethod
    async def START_MOVE_DEGREES(self, *args):
        raise NotImplementedError

    @abstractmethod
    async def START_SPEED_TIME(self, *args):
        raise NotImplementedError

    # convenience methods
    @property
    @abstractmethod
    def measure_start(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                            Union[float, int], float]]:
        """
        CONVENIENCE METHOD -- This method acts like a stopwatch. It returns the current
        raw "position" of the motor. It can be used to mark the start of an experiment.
        
        :return: The current time and raw "position" of the motor. In case a synchronized motor is
            used the dictionary holds a tuple with values for all motors (virtual and 'real').
        :rtype: Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int], float]]
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def measure_end(self) -> Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int],
                                                                          Union[float, int], float]]:
        """
        CONVENIENCE METHOD -- This method acts like a stopwatch. It returns the current
        raw "position" of the motor. It can be used to mark the end of a measurement.

        :return: The current time and raw "position" of the motor. In case a synchronized motor is
            used the dictionary holds a tuple with values for all motors (virtual and 'real').
        :rtype: Union[Tuple[Union[float, int], float], Tuple[Union[float, int], Union[float, int], Union[float, int], float]]
        """
        raise NotImplementedError

    def distance_start_end(self, gearRatio=1.0) -> Tuple:
        r = tuple(map(lambda x, y: (x - y) / gearRatio, self.measure_end, self.measure_start))
        return r

    def avg_speed(self, gearRatio=1.0) -> Tuple:
        startend = self.distance_start_end(gearRatio)
        dt = abs(startend[len(startend) - 1])
        r = tuple(map(lambda x: (x / dt), startend))
        return r
