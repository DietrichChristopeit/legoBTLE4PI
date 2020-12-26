from datetime import date
from time import localtime, strftime, time
from typing import List, Any

from bluepy import btle
from bluepy.btle import Scanner

from Logbuch.Log import Log
from Motor import Motor


class HubNo2:

    def __init__(self, kennzeichen: str = None):
        """Mit dieser Klasse wird ein neuer Controller des Typs Hub 2 für das Lego-Modell erzeugt. Es gibt auch andere
        Controller, z.B. WeDo2 oder Move Hub etc..

        :param kennzeichen:
            Dieser Parameter ist die sog. MAC-Adresse (z.B. 90:84:2B:5E:CF:1F) des Controllers.
        """
        if kennzeichen is not None:
            self.controller = btle.Peripheral(kennzeichen)
        else:
            self.controller = btle.Peripheral()

    def verbindeMitController(self, kennzeichen):
        if self.controller.getState() != 'conn':
            self.controller.connect(kennzeichen)

    @property
    def holeController(self):
        """Diese Funktion (a.k.a. Methode) gibt einen Verweis auf den Controllers zurück.


        :returns:
            Verweis auf den Hub
        """
        return self.controller

    @property
    def leseControllerName(self):
        """Diese Funktion (a.k.a. Methode) gibt den Namen des Controller zurück.

        :returns:
            Der Name des Controllers wird zurückgegeben.
        """
        return self.controller.readCharacteristic(7)

    def setzeLenkung(self, motor: Motor):
        pass
