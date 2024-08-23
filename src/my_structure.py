from threading import Lock
from queue import Queue


lock = Lock()


class MyQueue():
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, maxsize=25):
        self.maxsize = maxsize
        self.tqueue = Queue(maxsize=maxsize)
        self.queue = list()
        self._end_frame = None

    def __checkout(self):
        with lock:
            frame_id = self._end_frame
            while not self.tqueue.empty():
                frame_id, frame = self.tqueue.get_nowait()
                self.queue.append((frame_id, frame))
            self._end_frame = frame_id

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

    def _put(self, value):
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

