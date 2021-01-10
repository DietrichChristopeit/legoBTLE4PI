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

from abc import ABC, abstractmethod
from queue import Queue

import bluepy.btle

from MessageHandling.MessageQueue import MessageQueue


class MessagingEntity(ABC):

    @property
    @abstractmethod
    def uid(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def pipeline(self) -> Queue:
        raise NotImplementedError

    @pipeline.setter
    @abstractmethod
    def pipeline(self, pipeline: Queue):
        raise NotImplementedError

    @pipeline.deleter
    @abstractmethod
    def pipeline(self):
        raise NotImplementedError


class PublishingDelegate(MessagingEntity, bluepy.btle.DefaultDelegate):

    def __init__(self, friendlyName: str, pipeline: MessageQueue, acceptSpec=None):
        super(PublishingDelegate, self).__init__()
        bluepy.btle.DefaultDelegate.__init__(self)
        if acceptSpec is None:
            self.acceptSpec = ['']
        self._uid = id(self)
        self._friendlyName = friendlyName
        self._acceptSpec = acceptSpec
        self._pipeline = pipeline
        print("{} started...".format(friendlyName))

    def handleNotification(self, cHandle, data):
        self._pipeline.set_message(data.hex())

    @property
    def uid(self) -> int:
        return self._uid

    @property
    def pipeline(self) -> Queue:
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline: Queue):
        self._pipeline = pipeline

    @pipeline.deleter
    def pipeline(self):
        del self._pipeline
