from multiprocessing import Pipe, shared_memory

import ipdb
import numpy as np
import pickle

READINESS = 0
READING = 1
CLEANING = 2
EXCEPTION = 3


class Queue():
    """
    Fila para ser usada na classe VideoBufferRight
    """
    def __init__(self, conn_parent: Pipe, *, maxsize=0, lock=None):
        self.maxsize = maxsize
        self.conn = conn_parent
        self.queue = list()

        """O atributo status é a meneira com que se comunicamos com o processo. podendo
        assumir os seguintes valores:
            0 - status de prontidão isso significa que o processo pode iniciar a leitura a qualquer momento
                quando solicitado. Para a solicitação deve-se enviar True, para encerrar o processo deve-se
                enviar False, caso a menssagem enviada não for do tipo bool, uma exceção será levantada!
            1 - status de leitura, significa que o processo esta escrevendo na memória compartilhada.
            2 - status de limpeza, significa que o processo esta esperando uma confirmação para liberar as memórias
                compartilhadas, para isso deve-se enviar True
            3 - status de erro, devemo capturar a exceção.
        """
        self.status = 1

    def __checkout(self):
        while self.conn.poll():
            value = self.conn.recv()
            if isinstance(value, int):
                if value == READINESS:
                    self.status = READINESS
                elif value == READING:
                    self.status = READING
                elif value == CLEANING:
                    self.status = CLEANING
                    self.conn.send(True)
                elif value == EXCEPTION:
                    self.status = EXCEPTION

            elif isinstance(value, tuple):
                if self.status == READING:
                    (frame_id, shm_name, shape, dtype) = value
                    shm = shared_memory.SharedMemory(name=shm_name)
                    frame_tmp = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
                    #frame = np.copy(frame_tmp)
                    del frame_tmp
                    shm.close()
                    print(f'Pai fechou {shm_name}')
                    self.queue.append((frame_id, None))
                elif self.status == EXCEPTION:
                    exc, exc_info = pickle.loads(value)
                    print(f"Caught exception: {exc}")
                    print("Traceback:", exc_info)

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

