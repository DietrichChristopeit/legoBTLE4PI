from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor
from Konstanten.Anschluss import Anschluss
from MotorTyp.EinzelMotor import EinzelMotor

if __name__=='__main__':
    jeep = HubNo2('90:84:2B:5E:CF:1F')

    print('Controller name:', jeep.leseControllerName.decode('UTF-8'))

    vorderradantrieb = EinzelMotor(Anschluss.A, "Vorderradantrieb")
    hinterradantrieb = EinzelMotor(Anschluss.B, "Hinterradantrieb")
    lenkung = EinzelMotor(Anschluss.C, "Lenkung")
    characteristicV = vorderradantrieb.dreheMotorFuerT(2560, Motor.VOR, 50, Motor.BREMSEN)
    characteristicH = hinterradantrieb.dreheMotorFuerT(2560, Motor.VOR, 50, Motor.BREMSEN)
    jeep.holeController().writeCharacteristic(0x0e, bytes.fromhex(characteristicV), withResponse=False)
    jeep.holeController().writeCharacteristic(0x0e, bytes.fromhex(characteristicH), withResponse=False)
    sleep(6)
