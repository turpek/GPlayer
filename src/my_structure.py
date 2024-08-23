from multiprocessing import Pipe, shared_memory
from src.utils import BUFFER_RIGHT, BUFFER_LEFT
from threading import Lock
from queue import Queue

import ipdb
import numpy as np
import pickle

READINESS = 0
READING = 1
CLEANING = 2
EXCEPTION = 3


class MyQueue():
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, queue: Queue, lock: Lock, *, maxsize=0):
        self.maxsize = maxsize
        self.tqueue = queue
        self.queue = list()
        self._end_frame = None

    def __checkout(self):
        with self.lock:
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

