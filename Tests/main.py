from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor as Motorkonstante
from Konstanten.Anschluss import Anschluss
from Motor.EinzelMotor import EinzelMotor


class Testscripts:
    def __init__(self, MACaddress: str = '90:84:2B:5E:CF:1F'):
        """Testscript-Sammlung"""

        print("Verbinde mit {}...".format(MACaddress))
        self.jeep = HubNo2(MACaddress)

    def alleMotoren(self):
        """Testet alle Motoren.
            * Vorderradantrieb / Hinterradantrieb einzeln /gemeinsam für Zeiten t mit Kraft 50% / 70% / 100%
            * Lenkung links / rechts 55° / 100°

        :return:
        """
        print("Verbunden...")
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
        characteristicV = vorderradantrieb.dreheMotorFuerT(2560, Motorkonstante.VOR, 50, Motorkonstante.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicV), withResponse=True)
        sleep(1.5)
        print("Drehe Hinterräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        characteristicH = hinterradantrieb.dreheMotorFuerT(2560, Motorkonstante.VOR, 70, Motorkonstante.AUSLAUFEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicH), withResponse=False)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam für 4000ms mit voller Kraft rückwärts..")
        sleep(0.5)
        characteristicV = vorderradantrieb.dreheMotorFuerT(4000, Motorkonstante.ZURUECK, 100, Motorkonstante.BREMSEN)
        characteristicH = hinterradantrieb.dreheMotorFuerT(4000, Motorkonstante.ZURUECK, 100, Motorkonstante.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicV), withResponse=False)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicH), withResponse=False)
        sleep(6)
        print("Lenke um 55° mit halber Kraft nach links...")
        sleep(0.5)
        characteristicL = lenkung.dreheMotorFuerGrad(55, Motorkonstante.LINKS, 50, Motorkonstante.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicL), withResponse=False)
        sleep(1.5)
        print("Lenke um 100° mit halber Kraft nach rechts...")
        sleep(0.5)
        characteristicR = lenkung.dreheMotorFuerGrad(100, Motorkonstante.RECHTS, 50, Motorkonstante.BREMSEN)
        self.jeep.holeController.writeCharacteristic(0x0e, bytes.fromhex(characteristicR), withResponse=False)
        sleep(1.5)
        print("Trenne Verbindung...")
        self.jeep.holeController.disconnect()
        print("***Programmende***")


if __name__=='__main__':
    test = Testscripts()
    test.alleMotoren()
