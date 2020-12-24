from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor
from Konstanten.Port import Port
from MotorTyp.EinzelMotor import EinzelMotor

if __name__ == '__main__':
    #jeep = HubNo2('90:84:2B:5E:CF:1F')

    #print('Controller name:', jeep.leseControllerName.decode('UTF-8'))
    motor = EinzelMotor(Port.A, "Lenkung")
    motor.dreheMotorfuerMS(2560, Motor.VOR, 50, Motor.BREMSEN)
    motor.dreheMotorfuerGrad(360, Motor.VOR, 50, Motor.BREMSEN)

    sleep(6)
