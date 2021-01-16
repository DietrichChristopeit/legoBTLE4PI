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
import queue
from abc import ABC, abstractmethod
from queue import Queue

from bluepy import btle
from deprecated.sphinx import deprecated


class MessagingEntity(ABC):

    @property
    @abstractmethod
    def cmdRsltQ(self) -> Queue:
        raise NotImplementedError

    @cmdRsltQ.setter
    @abstractmethod
    def cmdRsltQ(self, cmdRsltQ: Queue):
        raise NotImplementedError

    @cmdRsltQ.deleter
    @abstractmethod
    def cmdRsltQ(self):
        raise NotImplementedError


class PublishingDelegate(btle.DefaultDelegate):
    def __init__(self, name: str, cmdRsltQ: queue.Queue):
        btle.DefaultDelegate.__init__(self)
        self._name = name
        self._cmdRsltQ = cmdRsltQ
        print("[{}]-[MSG]: STARTED...".format(name))
        return

    def __call__(self, *args, **kwargs):
        pass

    def handleNotification(self, cHandle, data):
        """This is the callback method that is invoked when commands produce results.
        This functionality only works if the Hub has previously issued a Notification-All request.

        :param cHandle:
            Specifies the Bluetooth handle of the original data.
        :param data:
            The received feedback (results) of a data sent. This data is then put into a queue.Queue and can be
            fetched from there (c.f. LegoBTLE.Controller.Hub).
        :return:
            None
        """
        # print(data.hex())
        self._cmdRsltQ.put(bytes.fromhex(data.hex()))
        return

    # @deprecated(reason="Unnecessary", version='1.1', action="Keep for now")
    # @property
    # def uid(self) -> int:
    #     """Once this was thought necessary
    #
    #     :return:
    #     """
    #     return self._uid
    @property
    def name(self) -> str:
        return self._name

    @property
    def cmdRsltQ(self) -> queue.Queue:
        return self._cmdRsltQ

    @cmdRsltQ.setter
    def cmdRsltQ(self, cmdRsltQ: queue.Queue):
        self._cmdRsltQ = cmdRsltQ
