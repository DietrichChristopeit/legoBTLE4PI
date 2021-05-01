"""
    legoBTLE.exceptions.Exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This Module shall provide an Exception Framework for things that can go wrong
    
    Things that can go wrong are for instance:
    
    * There is no Hub-Instance to connect to the Server.
    * Wrong answer from Server
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
"""

from typing import List

from legoBTLE.device.ADevice import ADevice
from legoBTLE.legoWP.types import C


class ExperimentException(Exception):
    """ExperimentException
    
    Thought to make specific exceptions that could happen during an execution of a list of motor commands more
    descriptive.
    
    Not well implemented
    """
    def __init__(self, message):
        self._message = message
        
        super().__init__(self._message)
        return
    
    def args(self):
        return self._message


class LegoBTLENoHubToConnectError(ExperimentException):
    """LegoBTLENoHubToConnectError
    
    Exception that is thrown when there is no hub defined to connect to.
    
    Not well implemented
    
    """
    
    def __init__(self, devices: List[ADevice], message: str = "No Hub given. Cannot connect to server "
                                                              "without one Hub Instance."):
        self._message = message
        self._devices = devices
        
        super().__init__(message=message)
        return
    
    def __str__(self):
        return f"{self._devices} -> {self._message}"


class ServerClientRegisterError(ExperimentException):
    """ServerClientRegisterError
    
    Exception that is thrown when there a client opens a connection,e.g., to send commands but did not request
    its registration.
    
    Not well implemented
    """
    
    def __init__(self, message: str):
        self._message = "CLIENT OPENED CONNECTION BUT DID NOT REQUEST REGISTRATION: " + message
        
        super().__init__(message=message)
        return
    
    def __str__(self):
        return f"{C.BOLD}{C.FAIL}{self._message}{C.ENDC}"
