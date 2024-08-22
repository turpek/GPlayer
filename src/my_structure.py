from multiprocessing import Pipe


class Queue():
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, conn_parent: Pipe, *, maxsize=0, lock=None):
        self.maxsize = maxsize
        self.conn = conn_parent
        self.queue = list()

    def __checkout(self):
        while self.conn.poll():
            value = self.conn.recv()
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

