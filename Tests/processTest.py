from multiprocessing import Process, Queue, Event
from random import uniform
from time import sleep


class Proctest(Process):
    def __init__(self, name: str, terminate: Event, q: Queue):
        super().__init__()
        self._name = name
        self._q = q
        self.terminate = terminate
        return

    def run(self):
        while not self.terminate.is_set():
            print("Name: {}:{}".format(Process.name, self._name))
            if not self._q.qsize() == 0:
                print("Queue: {}".format(self._q.get()))
            sleep(uniform(1, 3))

        print("Shutting down...")
        return


if __name__ == "__main__":
    terminate: Event = Event()
    q: Queue = Queue()
    p: Proctest = Proctest("TESTPROCESS", terminate, q)

    p.start()

    for i in range(1, 10):
        print("MAIN: putting {}".format(i))
        q.put(i)
        sleep(0.5)

    sleep(20)

    terminate.set()
    p.join()
