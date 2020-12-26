from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor
from Konstanten.Anschluss import Anschluss
from Motor.EinzelMotor import EinzelMotor

class Testscripts:
    def __init__(self, MACaddress:str='90:84:2B:5E:CF:1F'):
        self.jeep = HubNo2(MACaddress)

    def alleMotoren(self):

        print('Controller Name:', self.jeep.leseControllerName.decode('UTF-8'))

        vorderradantrieb = EinzelMotor(Anschluss.A, "Vorderradantrieb")
        print("Vorderradantrieb hinzugefügt...")
        hinterradantrieb = EinzelMotor(Anschluss.B, "Hinterradantrieb")
        print("Hinterradantrieb hinzugefügt...")
        lenkung = EinzelMotor(Anschluss.C, "Lenkung")
        print("Lenkung hinzugefügt...")
        sleep(1.5)
        print("Drehe Vorderräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        characteristicV = vorderradantrieb.dreheMotorFuerT(2560, Motor.VOR, 50, Motor.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicV), withResponse=False)
        sleep(1.5)
        print("Drehe Hinterräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        characteristicH = hinterradantrieb.dreheMotorFuerT(2560, Motor.VOR, 50, Motor.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicH), withResponse=False)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam für 4000ms mit halber Kraft rückwärts..")
        sleep(0.5)
        characteristicV = vorderradantrieb.dreheMotorFuerT(4000, Motor.ZURUECK, 50, Motor.BREMSEN)
        characteristicH = hinterradantrieb.dreheMotorFuerT(4000, Motor.ZURUECK, 50, Motor.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicV), withResponse=False)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicH), withResponse=False)
        sleep(6)
        print("Lenke um 55° mit halber Kraft nach links...")
        sleep(0.5)
        characteristicL = lenkung.dreheMotorFuerGrad(55, Motor.LINKS, 50, Motor.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicL), withResponse=False)
        sleep(1.5)
        print("Lenke um 100° mit halber Kraft nach rechts...")
        sleep(0.5)
        characteristicR = lenkung.dreheMotorFuerGrad(100, Motor.RECHTS, 50, Motor.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicR), withResponse=False)
        sleep(1.5)
        print("Trenne Verbindung...")
        self.jeep.holeController.disconnect()
        print("***Programmende***")



if __name__=='__main__':
    jeep =
