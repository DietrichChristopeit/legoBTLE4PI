from Hub import HubNo2
from Logbuch import Log
class Jeep:

    def __init__(self, kennzeichen: str = None, fahrtenbuch: Log = None, controller: HubNo2 = None):
        '''
        Mit diesem Modul (wird Klasse genannt) wird die Computerversion des Jeeps erestellt.

        :param kennzeichen: das Kennzeichen des Jeeps is seine sog. MAC-Adresse, z.B.: 90:84:2B:5E:CF:1F
        :param fahrtenbuch: hier kann ein vorhandenes Fahrtenbuch übergeben werden; falls dieser Parameter nicht angegeben
        wird, so wird ein Fahrtenbuch erstellt
        '''
        self.zeit = localtime()
        self.kennzeichen: str = kennzeichen
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
