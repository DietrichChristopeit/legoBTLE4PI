import enum

import MotorTyp
from Konstanten.Port import Port
from Konstanten.Motor import Motor


class EinzelMotor:

    def __init__(self, port: Port, name: str):
        '''

        :param port:
        :param name:
        '''
        self.port = port
        self.name = name

    @property
    def nameDesMotors(self):
        return self.nameDesMotors

    @property
    def anschlussDesMotors(self):
        return self.port

    def dreheMotorfuerMS(self, millisekunden: int, drehsinn: {Motor.VOR, Motor.ZURUECK, None}, power: int, zumschluss:
    {Motor.AUSLAUFEN, Motor.BREMSEN, Motor.FESTHALTEN, None}):
        '''
        
        :param millisekunden: 
        :param drehsinn: 
        :param power: 
        :param zumschluss: 
        :return: 
        '''
        print(millisekunden.to_bytes(2, byteorder='little', signed=False) .hex())
        return True

    def dreheMotorfuerGrad(self, grad: int, drehsinn: {Motor.VOR, Motor.ZURUECK, None}, power: int, zumschluss:
    {Motor.AUSLAUFEN, Motor.BREMSEN, Motor.FESTHALTEN, None}):
        '''

        :param grad: 
        :param drehsinn: 
        :param power: 
        :param zumschluss: 
        :return: 
        '''
        print(grad.to_bytes(4, byteorder='little', signed=False).hex())
        return True
