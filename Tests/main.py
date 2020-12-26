from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor as Motorkonstante
from Konstanten.Anschluss import Anschluss
from Motor.EinzelMotor import EinzelMotor
from Motor.KombinierterMotor import KombinierterMotor


class Testscripts:
    def __init__(self, MACaddress: str = '90:84:2B:5E:CF:1F', withDelegate: bool = False):
        """Testscript-Sammlung"""
        print("Verbinde mit {}...".format(MACaddress))
        self.jeep = HubNo2(MACaddress, withDelegate)

    def alleMotoren(self):
        """Testet alle Motoren.
            * Vorderradantrieb / Hinterradantrieb einzeln /gemeinsam für Zeiten t mit Kraft 50% / 70% / 100%
            * Lenkung links / rechts 55° / 100°

        :return:
        """
        print("Verbunden...")
        print('Controller Name:', self.jeep.leseControllerName.decode('UTF-8'))

        vorderradantrieb = EinzelMotor(Anschluss.A, "Vorderradantrieb")
        self.jeep.registriere(vorderradantrieb)
        print("Vorderradantrieb hinzugefügt...")
        hinterradantrieb = EinzelMotor(Anschluss.B, "Hinterradantrieb")
        self.jeep.registriere(hinterradantrieb)
        print("Hinterradantrieb hinzugefügt...")
        gemeinsamerAntrieb = KombinierterMotor(vorderradantrieb, hinterradantrieb, "gemeinsamer Motor")
        self.jeep.registriere(gemeinsamerAntrieb)
        print("gemeinsamer Motor hinzugefügt...")
        lenkung = EinzelMotor(Anschluss.C, "Lenkung")
        self.jeep.registriere(lenkung)
        print("Lenkung hinzugefügt...")
        sleep(1.5)
        print("Drehe Vorderräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        dreheVorderrad = vorderradantrieb.dreheMotorFuerT(2560, Motorkonstante.VOR, 50, Motorkonstante.BREMSEN)
        self.jeep.fuehreBefehlAus(dreheVorderrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Hinterräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        dreheHinterrad = hinterradantrieb.dreheMotorFuerT(2560, Motorkonstante.VOR, 70, Motorkonstante.AUSLAUFEN)
        self.jeep.fuehreBefehlAus(dreheHinterrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam für 4000ms mit voller Kraft rückwärts..")
        sleep(0.5)
        dreheVorderrad = vorderradantrieb.dreheMotorFuerT(4000, Motorkonstante.ZURUECK, 100, Motorkonstante.BREMSEN)
        dreheHinterrad = hinterradantrieb.dreheMotorFuerT(4000, Motorkonstante.ZURUECK, 100, Motorkonstante.BREMSEN)
        self.jeep.fuehreBefehlAus(dreheVorderrad, mitRueckMeldung=True)
        self.jeep.fuehreBefehlAus(dreheHinterrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam SYNCHRONISIERT für 4000ms mit voller Kraft vorwärts..")
        sleep(0.5)
        sleep(6)
        print("Lenke um 55° mit halber Kraft nach links...")
        sleep(0.5)
        lenkeLinks = lenkung.dreheMotorFuerGrad(55, Motorkonstante.LINKS, 50, Motorkonstante.BREMSEN)
        self.jeep.fuehreBefehlAus(lenkeLinks, mitRueckMeldung=True)
        sleep(1.5)
        print("Lenke um 100° mit halber Kraft nach rechts...")
        sleep(0.5)
        lenkeRechts = lenkung.dreheMotorFuerGrad(100, Motorkonstante.RECHTS, 50, Motorkonstante.BREMSEN)
        self.jeep.fuehreBefehlAus(lenkeRechts, mitRueckMeldung=True)
        sleep(1.5)

    def stopTests(self):
        print("Trenne Verbindung...")
        self.jeep.schalteAus()
        print("***Programmende***")


if __name__=='__main__':
    test = Testscripts('90:84:2B:5E:CF:1F', withDelegate=True)
    try:
        test.alleMotoren()
    except KeyboardInterrupt:
        test.stopTests()
