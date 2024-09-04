from abc import ABC, abstractmethod
from src.utils import BUFFER_CYCLE, BUFFER_LEFT, BUFFER_RIGHT, READER_ERROR
from time import sleep, time
import ipdb


class Checkout(ABC):
    def __init__(self, parent, event, lock):
        self.parent = parent
        self.event = event
        self.lock = lock
        self.values = list()
        self.value = None

    def __check_value_channel(self, value):
        return isinstance(value, tuple)

    def _check_codes(self, type_code: str) -> bool:
        for idx in range(len(self.values)):
            value = self.values[idx]
            if self.__check_value_channel(value):
                code, signal = value
                if code is type_code:
                    self.value = (code, signal)
                    self.values.pop(idx)
                    return True
        return False

    def _check_cicly(self, type_code: str) -> bool:
        code, _ = self.value
        return code is type_code
        return self._check_codes(type_code)

    def _check_timeout(self, timestart: float, timeout: float) -> bool:
        """Método simples para a checagem do tempo."""
        return time() - timestart > timeout

    def channel(self):
        if self.parent.poll():
            self.values.append(self.parent.recv())

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
            if self._check_timeout(start, obj.timeout):
                raise TimeoutError('Tempo de expera excedida')

    def error_channel(self):
        if self._check_codes(READER_ERROR):
            (_, (erro, exc_info)) = self.value
            self.value = None
            print(exc_info)
            raise erro

    @abstractmethod
    def check_queue(self):
        ...

    @abstractmethod
    def is_done(self):
        ...

    @abstractmethod
    def fill_buffer(self):
        ...

    @abstractmethod
    def is_finished(self):
        ...


class CheckoutRight(Checkout):
    def __init__(self, parent, event, lock):
        super().__init__(parent, event, lock)

    def check_queue(self, primary, secundary):
        frame_id = None
        with self.lock:
            while not secundary.empty():
                frame_id, frame = secundary.get_nowait()
                primary.append((frame_id, frame))

    def is_done(self, obj: object):
        if self._check_codes(BUFFER_RIGHT):
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


class CheckoutLeft(Checkout):
    def __init__(self, parent, event, lock):
        super().__init__(parent, event, lock)

    def cycle(self, obj: object):
        if self._check_codes(BUFFER_CYCLE):
            print('Ciclo concluido')
            obj._cycle = True

    def swap(self, obj: object):
        if obj.buffer.primary_is_empty() and obj._cycle and len(obj.queue) == 0:
            print('Fazendo a troca')
            obj.buffer.swap()
            obj._cycle = False

    def check_queue(self, main, auxiliary):
        frame_id = None
        with self.lock:
            if auxiliary.primary_is_full() and len(main) == 0:
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                while not auxiliary.primary_is_empty():
                    (ret, (frame_id, frame)) = auxiliary.get()
                    # print('Estou aqui', frame_id)
                    main.append((frame_id, frame))

    def is_done(self, obj: object):
        ...

    def fill_buffer(self, start_frame, last_frame, mapping):
        if start_frame <= last_frame and not self.event.is_set():
            print('>>>>>ENCHENDO O BUFFER<<<<<<<<<<<')
            self.parent.send(True)
            self.event.set()
            self.parent.send((start_frame, last_frame, mapping))

    def is_finished(self, obj: object):
        ...
