from abc import ABC, abstractmethod
from queue import Queue

from bluepy.btle import DefaultDelegate


class Notification(DefaultDelegate):

    def __init__(self):
        super().__init__()
        self.data = None
        self.notifications = None
        self.vPort = None
        self.vPort1 = None
        self.vPort2 = None

    def handleNotification(self, cHandle, data):
        print("DATA", data.hex())
        self.data = data.hex()
        if (list(data)[0]==9) and (list(data)[4]==2):
            self.vPort = list(data)[3]
            self.vPort1 = list(data)[7]
            self.vPort2 = list(data)[8]

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

    @abstractmethod
    def disp(self):
        pass


class Publisher(MessagingEntity):

    def disp(self):
        pass

    def __init__(self, uid: str, friendlyName: str, acceptSpec=None):
        if acceptSpec is None:
            self.acceptSpec = ['']
        self.uid = uid
        self.friendlyName = friendlyName
        self.acceptSpec = acceptSpec
        self.privateQueue = Queue


class Dispatcher:

    def __init__(self, entities: {MessagingEntity} = None):
        self.pipelines = {}
        self.entities = entities
        for e in self.entities:
            self.pipelines[e.uid] = Queue(20)

    def register(self, entities: {MessagingEntity}):
        self.entities.update(entities)
