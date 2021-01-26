from multiprocessing import Event
from multiprocessing.context import Process
from random import uniform
from time import sleep


class Proctest(Process):
    def __init__(self, name: str, terminate: Event):
        super().__init__()
        self._name = name
        self.terminate = terminate
        return

    def run(self):
        while not self.terminate.is_set():
            print("Name: {}:{}".format(Process.name, self.name))
            sleep(uniform(1, 3))

        print("Shutting down...")
        return


if __name__ == "__main__":
    terminate: Event = Event()
    p: Proctest = Proctest("TESTPROCESS", terminate)

    p.start()

    sleep(20)

    terminate.set()
    p.join()
