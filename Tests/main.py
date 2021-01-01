import signal
import sys
from time import sleep

from Hub.HubTypes import HubNo2
from Konstanten.Motor import Motor as MOTOR
from Konstanten.Anschluss import Anschluss
from Motor.EinzelMotor import EinzelMotor
from Motor.KombinierterMotor import KombinierterMotor


class EnumTest:
    def __init__(self):
        print("Links {}".format(MOTOR.LINKS.value))
        print("Rechts {}".format(MOTOR.RECHTS.value))
        print("Vor {}".format(MOTOR.VOR.value))
        print("Zurück {}".format(MOTOR.ZURUECK.value))


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
        vorderradantrieb = EinzelMotor(Anschluss.A, uebersetzung=2.67, name="Vorderradantrieb")
        self.jeep.registriere(vorderradantrieb)
        print("Vorderradantrieb Anschluss \"{}\" hinzugefügt...".format(vorderradantrieb.anschlussDesMotors))
        self.jeep.fuehreBefehlAus(vorderradantrieb.reset(), mitRueckMeldung=True)
        sleep(1)
        hinterradantrieb = EinzelMotor(Anschluss.B, uebersetzung=2.67, name="Hinterradantrieb")
        self.jeep.registriere(hinterradantrieb)
        print("Hinterradantrieb an Anschluss \"{}\" hinzugefügt...".format(hinterradantrieb.anschlussDesMotors))
        self.jeep.fuehreBefehlAus(hinterradantrieb.reset(), mitRueckMeldung=True)
        sleep(1)
        gemeinsamerAntrieb = KombinierterMotor(vorderradantrieb, hinterradantrieb, uebersetzung=2.67,
                                               name="Vorder- und Hinterrad gemeinsam")
        self.jeep.registriere(gemeinsamerAntrieb)
        print("gemeinsamer Motor: \"{}\" hinzugefügt...".format(gemeinsamerAntrieb.nameDesMotors))
        self.jeep.fuehreBefehlAus(gemeinsamerAntrieb.reset(), mitRueckMeldung=True)
        sleep(1)
        lenkung = EinzelMotor(Anschluss.C, uebersetzung=1.00, name="Lenkung")
        self.jeep.registriere(lenkung)
        print("Lenkung hinzugefügt...")
        self.jeep.fuehreBefehlAus(lenkung.reset(), mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Vorderräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        dreheVorderrad = vorderradantrieb.dreheMotorFuerT(2560, MOTOR.VOR, 50, MOTOR.BREMSEN)
        self.jeep.fuehreBefehlAus(dreheVorderrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Hinterräder für 2560ms mit halber Kraft vorwärts...")
        sleep(0.5)
        dreheHinterrad = hinterradantrieb.dreheMotorFuerT(2560, MOTOR.VOR, 70, MOTOR.AUSLAUFEN)
        self.jeep.fuehreBefehlAus(dreheHinterrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam NICHT SYNCHRONISIERT für 4000ms mit voller Kraft rückwärts..")
        sleep(0.5)
        dreheVorderrad = vorderradantrieb.dreheMotorFuerT(4000, MOTOR.ZURUECK, 100, MOTOR.AUSLAUFEN)
        dreheHinterrad = hinterradantrieb.dreheMotorFuerT(4000, MOTOR.ZURUECK, 100, MOTOR.BREMSEN)
        self.jeep.fuehreBefehlAus(dreheVorderrad, mitRueckMeldung=True)
        self.jeep.fuehreBefehlAus(dreheHinterrad, mitRueckMeldung=True)
        sleep(1.5)
        print("Drehe Vorder- und Hinterräder gemeinsam SYNCHRONISIERT für 4000ms mit voller Kraft vorwärts..")
        sleep(0.5)
        dreheGemeinsamenAntrieb = gemeinsamerAntrieb.dreheMotorFuerT(4000, MOTOR.VOR, 100, zumschluss=MOTOR.BREMSEN)
        self.jeep.fuehreBefehlAus(dreheGemeinsamenAntrieb, mitRueckMeldung=True)
        sleep(6)
        print("Lenke um 55° mit halber Kraft nach links...")
        sleep(0.5)
        lenkeLinks = lenkung.dreheMotorFuerGrad(55, MOTOR.LINKS, 50, MOTOR.BREMSEN)
        self.jeep.fuehreBefehlAus(lenkeLinks, mitRueckMeldung=True)
        sleep(1.5)
        print("Lenke um 100° mit halber Kraft nach rechts...")
        sleep(0.5)
        lenkeRechts = lenkung.dreheMotorFuerGrad(100, MOTOR.RECHTS, 50, MOTOR.BREMSEN)
        self.jeep.fuehreBefehlAus(lenkeRechts, mitRueckMeldung=True)
        sleep(1.5)
        Testscripts.stopTests(self.jeep)

    @staticmethod
    def stopTests(jeep: HubNo2):
        print("Trenne Verbindung...")
        jeep.schalteAus()
        print("***Programmende***")


if __name__=='__main__':

    test = Testscripts('90:84:2B:5E:CF:1F', withDelegate=True)
    test.alleMotoren()
