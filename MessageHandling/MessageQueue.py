import logging
import queue


class MessageQueue(queue.Queue):
    '''Diese Klasse ermöglicht das Versenden und Empfangen von Nachrichten (MessageHandling).

    '''

    def __init__(self, debug: bool = False, maxsize: int = 10):
        super().__init__(maxsize)
        self.debug = debug

    def get_message(self, name):
        dbg = logging.debug("%s:about to get from queue", name) if self.debug is True else print(name, "about to get from queue")
        value = self.get()

        dbg = logging.debug("%s:got %d from queue", name, value) if self.debug is True else print("{}:got {} from "
                                                                                                  "queue".format(name, value))
        return value

    def set_message(self, value, name):
        dbg = logging.debug("%s:about to add %d to queue", name, value) if self.debug is True else print(name, "setting data",
                                                                                                         value)
        self.put(value)

        dbg = logging.debug("%s:added %d to queue", name, value) if self.debug is True else ''
