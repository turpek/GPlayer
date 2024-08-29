"""Este módulo tem uma classe que implementa um buffer, onde terá dois
buffers internos que farão a gestão do objeto, de maneira ao Buffer
estár sempre cheio, para isso temos os seguintes atributos e métodos.


class Buffer:
    -primary: É uma Queue que define o buffer primario
    -secondary: É uma Queue que define o buffer segundario

    +secondary_is_empty() Bool: Método que retorna True se o buffer segundario estiver vazio

"""
from queue import Queue


class Buffer:
    def __init__(self, size=15):
        self.__primary = Queue(maxsize=size)
        self.__secondary = Queue(maxsize=size)

    def __primary_is_empty(self) -> bool:
        """
        Método privado que verifica se o buffer primario esta vazio.

        Returns:
            bool
        """
        return self.__primary.empty()

    def __primary_is_full(self) -> bool:
        """
        Método privado que verifica se o buffer primario esta cheio.

        Returns:
            bool
        """
        return self.__primary.full()

    def swap(self) -> bool:
        """
        Faz a troca dos buffers, se o primario estiver vazio e o segundario não,
        retornando True em caso de troca e False caso contrário.

        Returns:
            bool
        """
        if self.__primary_is_empty() and self.secondary_is_empty() is False:
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
        return self.__primary_is_empty() and self.secondary_is_empty()

    def full(self) -> bool:
        """
        Verifica se o buffer esta cheio.

        Returns:
            bool
        """
        return self.__primary_is_full() and self.secondary_is_full()

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

        if self.__primary_is_empty() is False:
            return (True, self.__primary.get_nowait())
        return (False, True)



