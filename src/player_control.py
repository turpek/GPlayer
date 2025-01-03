from loguru import logger
from numpy import ndarray
from src.buffer_left import VideoBufferLeft
from src.buffer_right import VideoBufferRight
from src.video_buffer import IVideoBuffer
import ipdb


class PlayerControl:
    def __init__(self, servant: IVideoBuffer, master: IVideoBuffer):
        self.servant = servant
        self.master = master
        self.frame_id = None
        self.__quit = False
        self.__paused = False
        self.__frame = None
        self.__delay = 35
        self.__default_delay = 35
        self.old = None

    def collect_frame(self) -> None:
        """
        Método onde o `master` faz a coleta do trabalho do `servant`.

        Returns:
            None
        """
        # if isinstance(self.__frame, ndarray) and not self.servant.is_task_complete():
        if isinstance(self.__frame, ndarray) and self.master[0] != self.frame_id:
            logger.debug(f'colentando o frame de id {self.frame_id}')
            self.master.put(self.frame_id, self.__frame)
            if self.servant.is_task_complete():
                self.frame_id = None
                self.__frame = None

    def __opencv_format(self, frame_id: int, frame: ndarray) -> tuple[bool, ndarray | None]:
        """
        Faz a converção para retornar o mesmo tipo que `cv2.VideoCapture.read`.

        Arggs:
            frame (ndarray): o frame coletado.
            frame_id (int): indice do frame coletado.

        Returns:
            tuple[bool, ndarray | None]
        """
        if isinstance(frame, ndarray):
            ls = [x[0] for x in self.servant._buffer._primary]
            ms = [x[0] for x in self.master._buffer._primary]
            print('servant', ls[:10])
            print('master:', ms[:10])
            self.__frame = frame
            self.frame_id = frame_id
            return True, frame
        return False, None

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
        self.collect_frame()
        if self.servant.is_task_complete() or self.pause():
            return False, None
        return self.__opencv_format(*self.servant.get())

    def rewind(self) -> None:
        """
        Controle para retroceder o vídeo.

        Esse metodo faz o swap entre os buffers, se servant for instancia de `VideoBufferRight`, com isso
        o buffer que faz a leitura reversa, ou seja, o `master`, passa a funcionar como o `servant`.

        Returns:
            None
        """
        if isinstance(self.servant, VideoBufferRight):
            logger.debug('setando o modo rewind')
            self.servant, self.master = self.master, self.servant

    def proceed(self) -> None:
        """
        Controle para retroceder o vídeo.

        Esse metodo faz o swap entre os buffers se `servant` for instancia de `VideoBufferRight`, com isso
        o buffer que faz a leitura correta, ou seja, o `master`, passa a funcionar como o `servant`.

        Returns:
            None
        """
        if isinstance(self.servant, VideoBufferLeft):
            logger.debug('setando o modo proceed')
            self.servant, self.master = self.master, self.servant

    def set_pause(self):
        logger.debug(f'setting the pause to {not self.__paused}')
        self.__paused = not self.__paused

    def pause(self) -> bool:
        return self.__paused

    def set_quit(self):
        logger.debug('preparando para sair...')
        self.__quit = True

    def quit(self) -> bool:
        return self.__quit

    def increase_speed(self) -> None:
        if self.__delay > 1:
            self.__delay -= 1
            speed = self.__default_delay / self.__delay
            logger.info(f'velocidade {speed:.2f}x {self.__delay}')

    def decrease_speed(self) -> None:
        self.__delay += 1
        speed = self.__default_delay / self.__delay
        logger.info(f'velocidade {speed:.2f}x {self.__delay}')

    def pause_delay(self) -> None:
        if self.__delay == 0:
            logger.debug('unpause by delay')
            self.__delay = self.__default_delay
        else:
            logger.debug('pause by delay')
            self.__delay = 0

    @property
    def delay(self) -> int:
        return self.__delay

    def remove_frame(self) -> tuple[int | None, ndarray | None]:
        logger.debug(f'servo {self.servant}')
        if isinstance(self.__frame, ndarray) and not self.pause():
            frame_id, frame = self.frame_id, self.__frame
            self.__frame = None
            self.frame_id = None
            return frame_id, frame
        elif not self.servant.is_task_complete():
            frame, ret = self.read()
            if ret is True:
                return self.remove_frame()
        return None, None
