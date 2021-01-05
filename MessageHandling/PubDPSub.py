import concurrent.futures
import logging
import threading
import time
from abc import ABC, abstractmethod
from queue import Queue

import bluepy.btle

from Geraet.Motor import Motor
from MessageHandling.Pipeline import Pipeline


class Notification(bluepy.btle.DefaultDelegate):

    def __init__(self):
        super(Notification, self).__init__()
        self.data = None
        self.notifications = None
        self.vPort = None
        self.vPort1 = None
        self.vPort2 = None

    def handleNotification(self, cHandle, data):
        print("DATA", data.hex())
        self.data = data.hex()
        if (list(self.data)[0]==9) and (list(self.data)[4]==2):
            self.vPort = list(self.data)[3]
            self.vPort1 = list(self.data)[7]
            self.vPort2 = list(self.data)[8]

    def holeNotification(self):
        if self.notifications is not None:
            return self.notifications
        else:
            return None

    def holeVPortInfo(self):
        return {self.vPort, self.vPort1, self.vPort2}

    # not sure about solution approach yet
    def decode_response(self, data: list):
        if data[2]==4:
            if (data[0]==9) and (data[4]==2):  # attached virtual Port
                self.notifications["HUB attached IO"]["VirtualPort"] = data[3]
                self.notifications["HUB attached IO"]["VirtualPort"]["Motor1"] = data[7]
                self.notifications["HUB attached IO"]["VirtualPort"]["Motor2"] = data[8]
            elif data[0]==15:
                self.notifications["HUB attached IO"]["NormalPort"] = data[3]


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


class Publisher(MessagingEntity, bluepy.btle.DefaultDelegate):

    def __init__(self, friendlyName: str, pipeline: Pipeline, acceptSpec=None):
        super(Publisher, self).__init__()
        if acceptSpec is None:
            self.acceptSpec = ['']
        self._uid = id(self)
        self._friendlyName = friendlyName
        self._acceptSpec = acceptSpec
        self._pipeline = pipeline
        print("In Publisher")

    def handleNotification(self, cHandle, data):
        self._pipeline.set_message(data, "Devices")

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


class Dispatcher:

    def __init__(self, name: str, motors: {Motor}):
        self.pipelines = {}
        self.entities = None
        self._motoren = motors

        for m in motors:
            self.pipelines[m.anschluss] = Queue(maxsize=20)

    def executeLoop(self):
        event = threading.Event()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.offerNotification, self.pipeline, event)
            futures = {executor.submit(m.processNotification, self.pipelines[m.anschluss], event): m for m in self._motoren}
            time.sleep(0.1)
            logging.info("Main: about to set event")
            event.set()

    def registerPipelines(self, entities: {MessagingEntity}):
        for e in entities:
            self.pipelines[e.uid] = Queue(maxsize=20)  # MessageEntities registered at Dispatcher
            e.pipeline = self.pipelines[e.uid]


class PublisherToDispatcherSubSystem:

    def __init__(self):
        self.dispatcher = Dispatcher("Dispatch notifications to KMotor attributes")
        self.publisher = Publisher("LEGO TECHNIC HUB publisher")
        self.dispatcher.registerPipelines({self.publisher})

    def executeLoop(self):
        pipeline_PubDisp = Pipeline()
        event = threading.Event()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.publisher, pipeline_PubDisp, event)
            executor.submit(self.dispatcher, pipeline_PubDisp, event)
            time.sleep(0.1)
            logging.info("Main: about to set event")
            event.set()
