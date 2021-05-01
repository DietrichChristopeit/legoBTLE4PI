"""
    legoBTLE.user.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~
    
    Holds several exception Modules
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
    
"""
from typing import List

from legoBTLE.device import ADevice
from legoBTLE.legoWP.types import C


class ExperimentException(Exception):
    
    def __init__(self, message):
        """Create a new :class:`ExperimentException`.
        
        Parameters
        ----------
        message : str
            The error message.
        """
        self._message = message
        
        super().__init__(self._message)
        return
    
    def __str__(self):
        return self._message
    
    def args(self):
        return self._message


class LegoBTLENoHubToConnectError(ExperimentException):
    
    def __init__(self, devices: List[ADevice], message: str = "No Hub given. Cannot connect to server "
                                                              "without one Hub Instance."):
        """Create a new :class:`LegoBTLENoHubToConnectError`
        
        Parameters
        ----------
        devices : List[ADevice]
            A list of devices
        message : str
            A exception message string
        """
        self._message = message
        self._devices = devices
        super().__init__(message=message)
        
        return
    
    def __str__(self):
        return f"{self._devices} -> {self._message}"


class ServerClientRegisterError(ExperimentException):
    
    def __init__(self, message: str):
        """Create a new :class:`ServerClientRegisterError`.
        
        Parameters
        ----------
        message : str
            The error message
        """
        self._message = "CLIENT OPENED CONNECTION BUT DID NOT REQUEST REGISTRATION: " + message
        super().__init__(message=message)
        return
    
    def __str__(self):
        return f"{C.BOLD}{C.FAIL}{self._message}{C.ENDC}"
