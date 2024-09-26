from array import array
from numpy import ndarray
from src.buffer_left import VideoBufferLeft
from src.buffer_right import VideoBufferRight
from src.frame_mapper import FrameMapper
from src.video_buffer import IVideoBuffer
from pathlib3x import Path
from time import sleep
from threading import Semaphore
import cv2
import ipdb


class VideoCon:
    def __init__(self, file_name: str, *, frames_mapping: list[int] = None, buffersize: int = 60, log: bool = False):

        self.__path = Path(file_name)
        self.__cap = cv2.VideoCapture(str(self.__path))
        self.__creating_window()

        self._mapping = self.set_mapping(frames_mapping)

        self.__semaphore = Semaphore()

        # Intanciando os Buffers responsaveis pelo gerenciamento dos frames.
        args = (self.__cap, self._mapping, self.__semaphore)
        self._slave = VideoBufferRight(*args, buffersize=buffersize, bufferlog=log)
        self._master = VideoBufferLeft(*args, buffersize=buffersize, bufferlog=log)

        # Iniciando a task e esperando que a mesma esteja concluida.
        self._slave.run()
        self._slave._buffer.wait_task()

        self.__frame_id = None
        self.frame = None
        self.__paused = False
        self.__quit = False
        self._delay = 1

    def __creating_window(self) -> None:
        """
        Cria a janela onde os frames serão exibidos.

        Returns:
            None
        """
        cv2.namedWindow('video', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('video', 720, 420)

    def join(self):
        self._master._buffer.wait_task()
        self._master.join()
        self._master._buffer.wait_task()
        self._slave.join()

    def set_mapping(self, frame_ids: list = None) -> None:
        """
        Define o mapping de frames que serão lidos e armazenados no buffer.

        Returns:
            None
        """
        frame_count = int(self.__cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_ids = frame_ids if isinstance(frame_ids, (list, tuple, array)) else list(range(frame_count))
        if hasattr(self, '_slave') and hasattr(self, '_master'):
            vbuffers = [self._slave, self._master]
            self._mapping.set_mapping(frame_ids, frame_count, vbuffers)
            return self._mapping
        else:
            return FrameMapper(frame_ids, frame_count)

    @property
    def frame_id(self) -> int:
        """
        Armazena o índice do frame atual lido no método read.

        Returns:
            int:
                - retorna um inteiro que representa o índice do frame atual.
        """
        return self.__frame_id

    def set(self, frame_id) -> None:
        """
        Define o vídeo para o frame especificado pelo índice 'frame_id'.

        Posiciona o vídeo no frame correspondente ao índice fornecido.
        O índice deve ser um valor inteiro maior ou igual a 0.

        Args:
            frame_id (int): O índice do frame para o qual o vídeo deve ser posicionado.
                            Deve ser um valor maior ou igual a 0.

        Returns:
            None
        """
        if isinstance(self._slave, VideoBufferRight):
            self._slave.set(frame_id)
            self._master.set(frame_id - 1)
            # self._slave.run()

    def read(self) -> tuple[bool, ndarray | None]:
        """
        Lê um frame de vídeo e retorna uma tupla contendo o estado da operação e o frame.

        A função tenta ler um frame de vídeo e retorna um booleano indicando o sucesso ou falha da operação.
        Se a leitura for bem-sucedida, o segundo elemento da tupla será o frame (como um `ndarray`).
        Caso contrário, o segundo elemento será `None`.

        Returns:
            tuple[bool, ndarray | None]:
                - O primeiro valor é um `bool` indicando se a operação foi bem-sucedida (`True`) ou não (`False`).
                - O segundo valor é um `ndarray` representando o frame lido, ou `None` se a operação falhar.
        """
        if self._slave.is_task_complete() or self.pause():
            return False, None

        frame_id, frame = self._slave.get()
        if isinstance(frame, ndarray):
            self._master.put(frame_id, frame)
            self.__frame_id = frame_id
            return True, frame
        return False, None

    def rewind(self) -> bool:
        """
        Controle para retroceder o vídeo.

        Esse metodo faz o swap entre os buffers, se slave for instancia de `VideoBufferRight`, com isso
        o buffer que faz a leitura reversa, ou seja, o `master`, passa a funcionar como o `slave`.

        Returns:
            bool:
                - Retorna True se a operação teve sucesso.
                - Retorna False se a operação falhou.
        """
        if isinstance(self._slave, VideoBufferRight):
            # Devemos retirar o frame do master e verificar se ele é igual
            # ao frame atual, se ele for
            self._slave, self._master = self._master, self._slave
            if self._slave[0] == self.frame_id:
                self.read()
            return True
        return False

    def resume(self) -> None:
        """
        Controle para retroceder o vídeo.

        Esse metodo faz o swap entre os buffers se `slave` for instancia de `VideoBufferRight`, com isso
        o buffer que faz a leitura correta, ou seja, o `master`, passa a funcionar como o `slave`.

        Returns:
            bool:
                - Retorna True se a operação teve sucesso.
                - Retorna False se a operação falhou.
        """
        if isinstance(self._slave, VideoBufferLeft):
            # Devemos retirar o frame do master e verificar se ele é igual
            # ao frame atual, se ele for
            self._slave, self._master = self._master, self._slave
            if self._slave[0] == self.frame_id:
                self.read()
            return True
        return False

    def pause(self):
        return self.__paused

    def quit(self):
        return self.__quit

    def _show(self, frame):
        cv2.imshow('video', frame)

    def show(self, flag, frame):
        if flag is True:
            self._show(frame)
        return cv2.waitKeyEx(self._delay)

    def control(self, key):
        if key == ord('d'):
            print('Resumir')
            self.resume()
        elif key == ord('a'):
            print('Voltar')
            self.rewind()
        elif key == ord('p'):
            self.__paused = not self.__paused
        elif key == ord('q'):
            self.__quit = True

    def loop(self):
        # self.rewind()
        while self.quit() is False:
            ret, frame = self.read()
            key = self.show(ret, frame)
            self.control(key)
        sleep(1)
        self.join()
        cv2.destroyAllWindows()
