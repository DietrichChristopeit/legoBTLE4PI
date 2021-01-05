#  MIT License
#
#  Copyright (c) 2021 Dietrich Christopeit
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

from Controller.HubType import HubType
from Logbuch import Log
from MotorenUndSensoren.Motor import EinzelMotor, KombinierterMotor


class Jeep:

    def __init__(self, kennzeichen: str, controller: HubType, lenkung: EinzelMotor =
    None, antrieb: KombinierterMotor = None):
        '''
        Mit diesem Modul (wird Klasse genannt) wird die Computerversion des Jeeps erestellt. Ein Jeep ist ein Fahrzeug,
        welches ein Kontrollmodul und verschiedene Motoren (Antrieb, Lenkung etc.) und/oder Sensoren (Abstandswarner etc.)
        besitzt.

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
            self.fahrtenbuch: Log = Log

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
