import logging
import queue


class Pipeline(queue.Queue):
    '''Diese Klasse ermöglicht das versenden und Empfangen von Nachrichten (MessageHandling).

    '''

    def __init__(self, debug: bool = False, maxsize: int = 10):
        super().__init__(maxsize)
        self.debug = debug

    def get_message(self, name):
        dbg = logging.debug("%s:about to get from queue", name) if self.debug is True else ''
        value = self.get()

        dbg = logging.debug("%s:got %d from queue", name, value) if self.debug is True else ''
        return value

    def set_message(self, value, name):
        dbg = logging.debug("%s:about to add %d to queue", name, value) if self.debug is True else ''
        self.put(bytes.fromhex(value))

        dbg = logging.debug("%s:added %d to queue", name, value) if self.debug is True else ''
