# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
import asyncio
from asyncio import Event
from asyncio import Queue

from LegoBTLE.Device.messaging import Message


class ABTLEDelegate:
    """
    Signal generator
        * (PUBLISHER to AHub)
        * employs a Q_SND_RETVAL_HUB (=== Q_RCV_RETVAL_BTLE in AHub) to publish CMD RETVALs to AHub
        * should PROBABLY be asyncio thread as I/O blocks
    """
    def __init__(self):
        return
    
    def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
        m: Message = Message(bytes.fromhex(data.hex()), True)
        return


class AHub:
    """
    COMMAND central:
        * offers functions to register devices
        * references a Q_RCV_CMD_DEVICE queue receiving commands issued TO the AHUB on a device (AMOTOR)
            * (SUBSCRIBER TO DEVICES)
        * employes a Q_SND_CMD_BTLE Queue sending commands gathered from all devices to BTLE
            * (PUBLISHER TO BTLE)
        * employes a Q_RCV_RETVAL_BTLE Queue receiving notifications from BTLE as CMD result values
            * (SUBSCRIBER TO BTLE)
        * employes a dispatch function to distribute RETVALs to devices
    """
    def __init__(self):
        return
    

class AMotor:
    """
    A Motor Device
        * offers the available commands (functions) of the Device
        * references a Q_SND_COMMAND_HUB (=== Q_RCV_CMD_DEVICE) to send CMDs (functions) to the AHub (PUBLISHER to AHUB)
        * employs a
    
    """
    
    def __init__(self):
        return
    
    