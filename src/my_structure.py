from abc import ABC, abstractmethod
from queue import Queue


class MyQueue(ABC):
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, maxsize=25):
        self.maxsize = maxsize
        self.tqueue = Queue(maxsize=maxsize)
        self.queue = list()
        self._end_frame = None

    @abstractmethod
    def _checkout(self):
        ...

    def speed_empty(self):
        if len(self.queue) == 0:
            return self.empty()
        else:
            return False

    def empty(self):
        self._checkout()
        return len(self.queue) == 0

    def full(self):
        self._checkout()
        return len(self.queue) == self.maxsize

    def get(self):
        self._checkout()
        if not self.empty():
            return self.queue.pop(0)

    @abstractmethod
    def _put(self, value):
        ...

    def qsize(self):
        self._checkout()
        return len(self.queue)


class MyQueueTest(MyQueue):
    def __init__(self, maxsize=25):
        super().__init__(maxsize=maxsize)

    def _checkout(self):
        frame_id = self._end_frame
        while not self.tqueue.empty():
            frame_id, frame = self.tqueue.get_nowait()
            self.queue.append((frame_id, frame))
        self._end_frame = frame_id
