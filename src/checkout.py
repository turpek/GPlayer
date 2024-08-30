from src.utils import BUFFER_LEFT, BUFFER_RIGHT, READER_ERROR
from time import sleep, time


class Checkout:
    def __init__(self, parent, event, lock):
        self.parent = parent
        self.event = event
        self.lock = lock
        self.value = None

    def check_queue(self, primary, secundary):
        frame_id = None
        with self.lock:
            while not secundary.empty():
                frame_id, frame = secundary.get_nowait()
                primary.append((frame_id, frame))

    def channel(self):
        if self.parent.poll():
            self.value = self.parent.recv()

    def __check_value_channel(self):
        return isinstance(self.value, tuple) and self.value is not None

    def __check_msg_code(self, type_code: str) -> bool:
        code, _ = self.value
        return code is type_code

    def __check_timeout(self, timestart: int, timeout: int) -> bool:
        """Método simples para a checagem do tempo."""
        return time() - timestart > timeout

    def timeout(self, obj: object) -> None:
        """
        Faz a checagem da queue durante timeout segundos,
        se não tiver nenhum elemento dentro da mesma um TimeoutError será levantado.

        obs. este método bloqueia o fluxo do programa, não implementa um timeout verdadeiramente.

            Args:
                obj IVideoBuffer: Classe que contém o atributo timeout

            Returns:
                None
        """
        start = time()
        while obj.speed_empty():
            sleep(0.01)
            if self.__check_timeout(start, obj.timeout):
                raise TimeoutError('Tempo de expera excedida')

    def error_channel(self):
        if self.__check_value_channel():
            if self.__check_msg_code(READER_ERROR):
                (_, (erro, exc_info)) = self.value
                self.value = None
                print(exc_info)
                raise erro

    def is_done(self, obj: object):
        if self.__check_value_channel():
            if self.__check_msg_code(BUFFER_RIGHT):
                (_, completed) = self.value
                obj._is_done = completed
                self.value = None

    def fill_buffer(self, start_frame, last_frame, mapping):
        if start_frame <= last_frame and not self.event.is_set():
            self.parent.send(True)
            self.event.set()
            self.parent.send((start_frame, last_frame, mapping))

    def is_finished(self, obj: object):
        if obj.frame_id() is not None:
            if obj.frame_id() >= obj.last_frame() and obj._is_done:
                obj._finished = True
