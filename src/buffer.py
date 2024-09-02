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
from queue import Queue
from threading import Lock


class Buffer:
    def __init__(self, size=15):
        # Queue que armazenam os frames
        self.__primary = Queue(maxsize=size)
        self.__secondary = Queue(maxsize=size)
        self.lock = Lock()

        # Queue para a comunicação do buffer com a thread
        self.__input = Queue(maxsize=1)

        # Queue para o envio de possíveis erros que venham a ocorrer na thread
        self.__error = Queue()

        self._task = Queue(maxsize=1)
        self._task.put_nowait(True)

    def __check_swap(self) -> bool:
        """
        Método privado usado para verificar se é necessario fazer o swap

        Returns:
            bool
        """
        return self.task_is_done() and self.primary_is_empty() and self.secondary_is_empty() is False

    def primary_is_empty(self) -> bool:
        """
        Método que verifica se o buffer primario esta vazio.

        Returns:
            bool
        """
        return self.__primary.empty()

    def primary_is_full(self) -> bool:
        """
        Método que verifica se o buffer primario esta cheio.

        Returns:
            bool
        """
        return self.__primary.full()

    def task_is_done(self) -> bool:
        """
        Verifica se o ciclo para encher o buffer secundary foi concluido.

        Returns:
            bool
        """
        with self.lock:
            task_is_done = self._task.get_nowait()
            self._task.put_nowait(task_is_done)
        return task_is_done

    def swap(self) -> bool:
        """
        Faz a troca dos buffers, se o primario estiver vazio e o segundario não,
        retornando True em caso de troca e False caso contrário.

        Returns:
            bool
        """
        if self.__check_swap():
            self.__primary, self.__secondary = self.__secondary, self.__primary
            return True
        return False

    def secondary_is_empty(self) -> bool:
        """
        Método que verifica se o buffer segundario esta vazio.

        Returns:
            bool
        """
        return self.__secondary.empty()

    def secondary_is_full(self) -> bool:
        """
        Método que verifica se o buffer segundario esta cheio.

        Returns:
            bool
        """
        return self.__secondary.full()

    def empty(self) -> bool:
        """
        Verifica se o buffer esta cheio.

        Returns:
            bool
        """
        return self.primary_is_empty() and self.secondary_is_empty()

    def full(self) -> bool:
        """
        Verifica se o buffer esta cheio.

        Returns:
            bool
        """
        return self.primary_is_full() and self.secondary_is_full()

    def put(self, value: any) -> None:
        """
        Método para colocar um valor no buffer.

        Args:
            value any: o valor a ser colocado no buffer.

        Returns:
            bool
        """
        self.__secondary.put_nowait(value)

    def get(self) -> tuple[bool, any]:
        """
        Retorna uma tupla contendo o resultado de uma operação de recuperação do buffer.

        A tupla possui dois elementos:
        - O primeiro elemento (índice 0) é um valor booleano indicando se a operação foi bem-sucedida.
        - O segundo elemento (índice 1) é o valor armazenado no buffer, que pode ser de qualquer tipo.

        Returns:
            tuple[bool, any]: Uma tupla onde o primeiro elemento indica o sucesso da operação
            e o segundo elemento contém o valor recuperado do buffer.
        """

        if self.primary_is_empty() is False:
            return (True, self.__primary.get_nowait())
        return (False, True)

    def send(self, data: any) -> None:
        """
        Método para enviar dados para a thread, como a queue onde é armazenado os dados tem tamanho 1,
        verifique com o método poll sé a dados ainda a serem lidos, antes de colocar mais dados e assim
        não travar o fluxo do programa


        Args:
            data any: os dados a serem enviados.

        Returns:
            None
        """
        with self.lock:
            self.__input.put(data)

    def recv(self) -> any:
        """
        Método para receber os dados envidos pelo método send

        Returns:
            any
        """
        with self.lock:
            return self.__input.get()

    def poll(self) -> bool:
        """
        Verifica se a dados a serem lidos

        Returns:
            bool
        """
        with self.lock:
            return self.__input.qsize() == 1
