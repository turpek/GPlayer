from array import array
from loguru import logger
from src.buffer_left import VideoBufferLeft
from src.buffer_right import VideoBufferRight
from src.frame_mapper import FrameMapper
from src.player_control import PlayerControl
from src.trash import Trash
from src.video_command import (
    Invoker,
    FrameRemoveOrchestrator,
    FrameUndoOrchestrator,
    DecreaseSpeedCommand,
    IncreaseSpeedCommand,
    PauseDelayCommand,
    RemoveFrameCommand,
    RestoreDelayCommand,
    RewindCommand,
    PauseCommand,
    ProceesCommand,
    QuitCommand,
    UndoFrameCommand
)
from pathlib3x import Path
from time import sleep
from threading import Semaphore
import cv2


class VideoCon:
    def __init__(self, file_name: str, *, frames_mapping: list[int] = None, buffersize: int = 60, log: bool = False):

        self.__path = Path(file_name)
        self.__cap = cv2.VideoCapture(str(self.__path))
        self.__creating_window()

        if not frames_mapping:
            frames_mapping = list(range(int(self.__cap.get(cv2.CAP_PROP_FRAME_COUNT))))
        self._mapping = self.set_mapping(frames_mapping)

        self.__semaphore = Semaphore()

        # Intanciando os Buffers responsaveis pelo gerenciamento dos frames.
        args = (self.__cap, self._mapping, self.__semaphore)
        self._slave = VideoBufferRight(*args, buffersize=buffersize, bufferlog=log)
        self._master = VideoBufferLeft(*args, buffersize=buffersize, bufferlog=log)
        self.command = Invoker()
        self.__player = PlayerControl(self._slave, self._master)
        self.__trash = Trash(self.__cap, self.__semaphore, int(self.__cap.get(cv2.CAP_PROP_FRAME_COUNT)), buffersize=20)
        # receiver = PlayerControlReceiver(self.__player)
        self.set_commands(self.__player, self._mapping, self.__trash)

        # Iniciando a task e esperando que a mesma esteja concluida.
        self._slave.run()
        self._slave._buffer.wait_task()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sleep(1)
        self.join()
        cv2.destroyWindow('videoseq')

    def __creating_window(self) -> None:
        """
        Cria a janela onde os frames serão exibidos.

        Returns:
            None
        """
        cv2.namedWindow('videoseq', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('videoseq', 720, 420)

    def join(self):
        self._master.join()
        self._slave.join()
        self.__trash.join()

    @property
    def frame_id(self):
        return self.__player.frame_id

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
            self._master.set(frame_id)
            # self._slave.run()

    def _show(self, frame):
        cv2.imshow('videoseq', frame)

    def show(self, flag, frame):
        if flag is True:
            logger.info(f'exibindo o frame de id {self.frame_id}')
            logger.info(f'servo -> {self.__player.servant} | mestre -> {self.__player.master}')
            self._show(frame)
        return self.control(cv2.waitKeyEx(self.__player.delay))

    def set_commands(self, player: PlayerControl, frame_mapper: FrameMapper, trash: Trash) -> None:
        frame_orchestrator = FrameRemoveOrchestrator(player, frame_mapper, trash)
        frame_undo = FrameUndoOrchestrator(player, frame_mapper, trash)
        command = self.command
        command.set_command(ord('p'), PauseCommand(player))
        command.set_command(ord('q'), QuitCommand(player))
        command.set_command(ord('a'), RewindCommand(player))
        command.set_command(ord('d'), ProceesCommand(player))
        command.set_command(ord(']'), IncreaseSpeedCommand(player))
        command.set_command(ord('['), DecreaseSpeedCommand(player))
        command.set_command(ord(' '), PauseDelayCommand(player))
        command.set_command(ord('='), RestoreDelayCommand(player))
        command.set_command(ord('x'), RemoveFrameCommand(frame_orchestrator))
        command.set_command(ord('u'), UndoFrameCommand(frame_undo))

    def control(self, key):
        self.command.executor_command(key)
        return key

    def read(self):
        return self.__player.read()

    def quit(self):
        return self.__player.quit()
