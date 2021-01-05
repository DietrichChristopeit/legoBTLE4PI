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
