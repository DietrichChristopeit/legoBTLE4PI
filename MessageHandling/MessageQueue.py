import logging
import queue


class MessageQueue(queue.Queue):
    '''Diese Klasse ermöglicht das Versenden und Empfangen von Nachrichten (MessageHandling).

    '''

    def __init__(self, debug: bool = False, maxsize: int = 10):
        super().__init__(maxsize)
        self.debug = debug

    def get_message(self, name):
        print("{}: ABOUT to get from queue".format(name))
        value = self.get()
        print("{}: GOT DATA: {} from queue".format(name, value))
        return value

    def set_message(self, value, name):
        print("{}: ABOUT to set data: {}".format(name, value))
        self.put(value)
        print("{}: HAS set data: {}".format(name, value))
