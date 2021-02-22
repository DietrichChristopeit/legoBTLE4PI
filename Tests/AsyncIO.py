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
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT_TYPE SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
import asyncio
from asyncio import Event
from asyncio import Queue


class AHub:
    
    def __init__(self, address: str = '90:84:2B:5E:CF:1F', name: str = 'Hub', cmdQ: Queue = None,
                 item_avail: Event = None, terminate: Event = None, debug: bool = False):
        self._E_HUB_NOFIFICATION_RQST_DONE: Event = Event()
        self._address = address
        self._name = name
        self._cmdQ = cmdQ
        self._Q_result: Queue = Queue(maxsize=-1)
        self._E_ITEM_AVAIL = item_avail
        self._E_TERMINATE: Event = terminate
        
        self._debug = debug
        MSG((self._name, self._address), msg="[{}]-[MSG]: TRYING TO CONNECT TO {}...", doprint=True, style=DBY())
        self._dev: btle.Peripheral = btle.Peripheral(address)
        MSG((self._name, self._address), msg="[{}]-[MSG]: CONNECTION SUCCESSFUL TO {}...", doprint=True, style=DBG())
        self._officialName: str = self._dev.readCharacteristic(0x07).decode("utf-8")
        MSG((self._name, self._officialName), msg="[{}]-[MSG]: OFFICIAL NAME: {}", doprint=True, style=DBB())
        self._registeredDevices = []
        
        self._Q_CMDRSLT: Queue = Queue(maxsize=-1)
        self._BTLE_DelegateNotifications = self.BTLEDelegate(self._Q_CMDRSLT)
        self._dev.withDelegate(self._BTLE_DelegateNotifications)
        
        return
    
    class BTLEDelegate(btle.DefaultDelegate):
        
        def __init__(self, Q_CMDRSLT: Queue, E_ITEM_AVAIL: Event):
            super().__init__()
            self._Q_BCMDRSLT: Queue = Q_CMDRSLT
            self._E_ITEM_AVAIL: Event = E_ITEM_AVAIL
            return
        
        def handleNotification(self, cHandle, data):  # Eigentliche Callbackfunktion
            try:
                m: Message = Message(bytes.fromhex(data.hex()), True)
                self._Q_BCMDRSLT.put(m, timeout=.0005)
                self._E_ITEM_AVAIL.set()
            except Full:
                MSG((), msg="Collision...", doprint=True, style=DBR())
                pass
            return
