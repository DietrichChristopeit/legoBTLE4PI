from datetime import date
from time import localtime, strftime, time
from typing import List, Any

from bluepy import btle
from bluepy.btle import Scanner

from Logbuch.Log import Log


class HubNo2:

    def __init__(self, kennzeichen: str = None):
        if kennzeichen is not None:
            self.controller = btle.Peripheral(kennzeichen)
        else:
            self.controller = btle.Peripheral()

    def verbindeMitController(self, kennzeichen):
        if self.controller.getState() != 'conn':
            self.controller.connect(kennzeichen)

    def holeController(self):
        '''
        Diese Funktion (wird Methode genannt) gibt einen Verweis auf den Controllers zurück.

        :return: Verweis auf den Hub
        '''
        return self.controller

    @property
    def leseControllerName(self):
        '''
        Diese Funktion (wird Methode genannt) gibt den Namen des Controller zurück.

        :return: Der Name des Controller wird zurückgegeben.
        '''
        return self.controller.readCharacteristic(7)
