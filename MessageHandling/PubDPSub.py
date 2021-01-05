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
        if acceptSpec is None:
            self.acceptSpec = ['']
        self._uid = id(self)
        self._friendlyName = friendlyName
        self._acceptSpec = acceptSpec
        self._pipeline = pipeline
        print("{} started...".format(friendlyName))

    def handleNotification(self, cHandle, data):
        self._pipeline.set_message(data.hex(), "[HUB]-[SND]")

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
