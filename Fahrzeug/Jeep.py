from Hub import HubTypes
from Logbuch import Log
from Motor import EinzelMotor, KombinierterMotor


class Jeep:

    def __init__(self, kennzeichen: str, controller: HubTypes, fahrtenbuch: Log = None, lenkung: EinzelMotor =
    None, antrieb: KombinierterMotor = None):
        '''
        Mit diesem Modul (wird Klasse genannt) wird die Computerversion des Jeeps erestellt.

        :param kennzeichen: das Kennzeichen des Jeeps is seine sog. MAC-Adresse, z.B.: 90:84:2B:5E:CF:1F
        :param fahrtenbuch: hier kann ein vorhandenes Fahrtenbuch übergeben werden; falls dieser Parameter nicht angegeben
        wird, so wird ein Fahrtenbuch erstellt
        '''
        self.kennzeichen: str = kennzeichen
        self.controller = controller
        self.lenkung = lenkung
        self.antrieb = antrieb
        self.zeit = localtime()

        self.steuerung: btle.Peripheral = None
        self.status: str = ''
        self.scanner: Scanner = Scanner()
        self.devrssi: List[Any] = []

        if fahrtenbuch is not None:
            self.fahrtenbuch: Log = fahrtenbuch
            self.fahrtenbuch.eintragHinzufuegen(
                    [strftime('%d.%m.%Y', localtime()), strftime('%H:%M:%S', localtime()), 'ein neuer Jeep wurde erzeugt'])
        else:
            self.fahrtenbuch: Log = Log(
                    [strftime('%d.%m.%Y', localtime()), strftime('%H:%M:%S', localtime()), 'ein neuer Jeep wurde erzeugt'],
                    None)

        if self.kennzeichen is None:
            self.steuerung: btle.Peripheral = btle.Peripheral()
            self.fahrtenbuch.eintragHinzufuegen(
                    [strftime('%d.%m.%Y', localtime()), strftime('%H:%M:%S', localtime()), 'Bluetooth-Steuerung nicht verbunden'])
            self.status = 'Bluetooth-Steuerung nicht verbunden'
        else:
            self.steuerung: btle.Peripheral = btle.Peripheral(self.kennzeichen)
            self.fahrtenbuch.eintragHinzufuegen(
                    [strftime('%d.%m.%Y', localtime()), strftime('%H:%M:%S', localtime()),
                     'Bluetooth-Steuerung verbunden: ' + str(self.kennzeichen)])
            self.status = 'verbunden mit Adresse(MAC) ' + str(self.kennzeichen)
