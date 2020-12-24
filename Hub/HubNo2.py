from datetime import date
from time import localtime, strftime, time
from typing import List, Any

from bluepy import btle
from bluepy.btle import Scanner

from Logbuch.Log import Log


class HubNo2:


    def sucheUndVerbindeJeep(self):
        result: bool = False
        devices: List[Any] = []
        try:
            devices = self.scanner.scan(10)
            result = True
        except Exception as e:
            print("BLE error: ", e)
            devices = []
        tempdev: List[Any] = []
        temprssi: List[Any] = []
        for dev in devices:
            try:
                if self.bledev==int(dev.iface):
                    temprssi.append(dev.rssi)
                    tempdev.append(str(dev.addr).lower().strip())
            except:
                pass
        self.devices = tempdev
        self.devrrsi: List[Any] = temprssi
        return result

    def verbindeZuJeep(self, kennzeichen: str):
        self.kennzeichen = kennzeichen
        self.steuerung.connect(self.kennzeichen)
        self.fahrtenbuch.eintragHinzufuegen(
                [strftime('%d.%m.%Y', localtime()), strftime('%H:%M:%S', localtime()),
                 'Bluetooth-Steuerung verbunden: ' + str(self.kennzeichen)])
        self.status = 'verbunden mit Adresse(MAC) ' + str(self.kennzeichen)

    def holeSteuerung(self):
        return self.steuerung

    def jeepStatus(self):
        return self.status

    def oeffneFahrtenbuch(self):
        '''
        Mit dieser Methode (wird Methode genannt) kann das Fahrtenbuch angefordert werden.

        :return: das Fahrtenbuch wird zurückgegeben
        '''
        return self.fahrtenbuch

    def speichereFahrtenbuch(self, dateiname: str = None):
        '''
        Mit dieser Methode (wird Methode genannt) kann das Fahrtenbuch in einem Format gespeichert werden, so dass es mit Excel etc. anzuschauen ist.

        :param dateiname: der komplette Pfad mit Dateiname, wo das Fahrtenbuch abgespeichert werden soll
        z.B.: ~/Desktop/Fahrtenbuch.csv

        :return: es wird kein Resultat zurückgegeben
        '''
        return self.fahrtenbuch.speichereLogbuch(dateiname)

    def __str__(self):
        jeepInfo = "Zeitpunkt: {0}, Kennzeichen: {1}, aktueller Status: {2}".format(strftime('%d.%m.%Y - %H:%M:%S',
                                                                                             localtime()), self.kennzeichen,
                                                                                    self.status)
