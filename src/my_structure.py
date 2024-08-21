from multiprocessing import Lock, Process, SimpleQueue as Pqueue
from time import sleep
import ipdb


class Queue():
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, *, maxsize=0, lock=None):
        self.maxsize = maxsize
        self.lock = lock if lock else Lock()
        self.pqueue = Pqueue()
        self.queue = list()

    def __checkout(self):
        with self.lock:
            sleep(0)
            while not self.pqueue.empty():
                value = self.pqueue.get()
                self.queue.append(value)

    def empty(self):
        self.__checkout()
        return len(self.queue) == 0

    def full(self):
        self.__checkout()
        return len(self.queue) == self.maxsize

    def get(self):
        self.__checkout()
        if not self.empty():
            return self.queue.pop(0)

    def put(self, value):
        """put(value) metodo para inserção manual dos dados na fila, tal metodo
         tem a preferencia na fila, ou seja, o dado eh colocado no inicio da fila
        """
        self.__checkout()
        if self.full():
            _ = self.queue.pop()
        self.queue.insert(0, value)

    def qsize(self):
        self.__checkout()
        return len(self.queue)

