import csv
from typing import Any, List


class Log:
    '''
    Dieses Modul (wird Klasse, Class genannt) stellt das Logbuch für den Jeep dar.
    Damit kann über die gesamte Fahrtdauer nachvollzogen werden, was alles passiert is.
    '''

    def __init__(self, eintrag: List[Any] = [], kolonnen: List[str] = []):
        '''
        Diese Funktion (wird Methode genannt) erstellt ein neues Logbuch.

        :param eintrag: ein erster Eintrag, z.B.: ['20.12.2020', '15:30', 'Auto verbunden']
        :param kolonnen: die Namen der Spalten, z.B.: ['Datum', 'Uhrzeit', 'Aktion']
        '''
        self.logEintraege: List[Any] = eintrag
        self.kolonnen = kolonnen
        self.logEintraege.append(eintrag)

    def eintragHinzufuegen(self, eintrag):
        '''
        Diese Funktion (wird Methode genannt) fügt einen Eintrag in das Logbuch hinzu.

        :param eintrag: ein Eintrag, z.B.: ['20.12.2020', '15:30', 'Auto verbunden']
        :return:
        '''
        self.logEintraege.append(eintrag)

    def sucheEintrag(self, suchwort):
        ergebnisliste = []
        for zeile in self.logEintraege:
            for zelle in zeile:
                if zelle == suchwort:
                    ergebnisliste.append(zeile)
                    break
        return ergebnisliste

    def loescheLogbuch(self):
        self.logEintraege = None

    def speichereLogbuch(self, dateiname: str = None):
        with open(dateiname, 'w') as f:
            # using csv.writer method from CSV package
            write = csv.writer(f)
            write.writerow(self.kolonnen)
            write.writerows(self.logEintraege)

    def __str__(self):
        return str(self.logEintraege)
