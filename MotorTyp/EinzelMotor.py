from Konstanten.Motor import Motor
from Konstanten.Anschluss import Anschluss


class EinzelMotor:

    def __init__(self, port: Anschluss, name: str):
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

    def dreheMotorFuerT(self, millisekunden: int, drehsinn: Motor = Motor.VOR, power: int = 100,
                         zumschluss: Motor = Motor.BREMSEN):
        '''
        
        :param millisekunden: 
        :param drehsinn: 
        :param power: 
        :param zumschluss: 
        :return: 
        '''

        power = drehsinn.value * power

        characteristic = '0c0081' + '{:02x}'.format(self.anschlussDesMotors.value) + '1109' + millisekunden.to_bytes(2, byteorder='little',
                                                                                                                     signed=False).hex() \
                         + power.to_bytes(1, byteorder='little', signed=True).hex() + '64' + '{:02x}'.format(zumschluss.value) + '03'

        return characteristic

    def dreheMotorFuerGrad(self, grad: int, drehsinn: {Motor.VOR, Motor.ZURUECK, None}, power: int, zumschluss:
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
