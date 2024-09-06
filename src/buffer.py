"""Este módulo tem uma classe que implementa um buffer, onde terá dois
buffers internos que farão a gestão do objeto, de maneira ao Buffer
estár sempre cheio, para isso temos os seguintes atributos e métodos.


class Buffer:
    -primary: É uma Queue que define o buffer primario
    -secondary: É uma Queue que define o buffer segundario


    -primary_is_empty() bool: Método que retorna True se o buffer segundario estiver vazio.
    -primary_is_full() bool: Método que retorna True se o buffer segundario estiver cheio.
    +secondary_is_empty() bool: Método que retorna True se o buffer segundario estiver vazio.
    +secondary_is_full() bool: Método que retorna True se o buffer segundario estiver cheio.
    +empty() bool: Retorna True se o buffer estiver vazio.
    +full() bool: Retorna True se o buffer estiver cheio.
    +put() None: Coloca um dado no buffer.
    +get() tuple[Bool, any]: Retorna uma tupla, onde o primeiro valor representa o sucesso do método
        e o segundo o valor armazenado.
    +swap() bool: Faz a troca se necessario entre os dois buffers, retornando True se a mesma for realizada
        e False caso contrário.

"""
from abc import ABC, abstractmethod
from collections import deque
from queue import Queue
from src.channel import Channel1
from threading import Lock, Semaphore


class Buffer(ABC, Channel1):
    def __init__(self, semaphore: Semaphore, *,maxsize: int=15, log: bool=False):
        # Criando um deque e uma Queue onde os frames serão armazenados
        self.maxsize = maxsize
        self.log = log
        self._primary = deque(list(), maxlen=maxsize)
        self._secondary = Queue(maxsize=maxsize)
        self.lock = Lock()
        self.semaphore = semaphore

        # Queue para o envio de possíveis erros que venham a ocorrer na thread
        self._error = Queue()

        self.__task= Queue(maxsize=1)
        self.__task.put_nowait(True)

    def __getitem__(self, var):
        return self._primary[var]

    def sput(self, value: any) -> None:
        """
        Método interno para preencher o buffer segundario.

        Args:
            value (any): dado a ser inserido no buffer

        Returns:
            None
        """
        self._secondary.put(value)

    def set(self) -> None:
        """
        Método para setar atributos que tem relação com inicio da task

        Returns:
            None
        """
        self.semaphore.acquire()
        self.task_is_done(False)

    def clear(self) -> None:
        """
        Método para setar atributos que tem relação com o fim da task

        Returns:
            None
        """
        self.semaphore.release()
        self.task_is_done(True)

    def task_is_done(self, value: bool=None) -> bool:
        """
        Verifica se o ciclo para encher o buffer secundary foi concluido.

        Returns:
            bool
        """
        with self.lock:
            task_is_done = self.__task.get_nowait()
            if isinstance(value, bool):
                self.__task.put_nowait(value)
            else:
                self.__task.put_nowait(task_is_done)
        return task_is_done

    def sempty(self) -> bool:
        """
        Verifica se o buffer segundario está vazio.

        Returns:
            bool
        """
        return self._secondary.empty()

    def empty(self) -> bool:
        """
        Verifica se o buffer está vazio.

        Returns:
            boll
        """
        return len(self.deque) == 0

    def full(self) -> bool:
        """
        Verifica se o buffer está cheio.

        Returns:
            boll
        """
        return len(self.deque) == self.deque.maxlen

    @abstractmethod
    def _put(self, value: any) -> None:
        ...

    def put(self, value: any) -> None:
        ...

    @abstractmethod
    def _get(self) -> any:
        ...

    def get(self) -> any:
        ...


class FakeBuffer(Buffer):
    def __init__(self, semaphore: Semaphore, *, maxsize: int=25, log: bool=False):
        super().__init__(semaphore, maxsize=maxsize, log=log)

    def _put(self) -> None:
        ...

    def _get(self) -> any:
        ...
