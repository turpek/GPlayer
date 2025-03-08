from loguru import logger
from src.playlist import Playlist
from src.video_command import (
    Invoker,
    DecreaseSpeedCommand,
    IncreaseSpeedCommand,
    NextVideoCommand,
    PauseDelayCommand,
    PrevVideoCommand,
    RemoveFrameCommand,
    RestoreDelayCommand,
    RewindCommand,
    PauseCommand,
    ProceesCommand,
    QuitCommand,
    UndoFrameCommand
)
from src.manager import VideoManager
from src.video_controller import VideoController
from time import sleep
import cv2


class VideoCon:
    def __init__(self, video: str | Playlist, *, frames_mapping: list[int] = None, buffersize: int = 60, log: bool = False):

        self.__playlist = video if isinstance(video, Playlist) else Playlist([video])
        self.__log = log
        self.__buffersize = buffersize
        self.__creating_window()

        self.__video_manager = VideoManager(buffersize, log)
        self.__video_controller = VideoController(self.__playlist,
                                                  frames_mapping,
                                                  self.__video_manager)

        self.command = Invoker()
        self.set_commands(self.__video_controller)

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
        self.__video_controller.join()

    @property
    def frame_id(self):
        return self.__video_controller.frame_id

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
        self.__video_controller.set_frame(frame_id)

    def _show(self, frame):
        cv2.imshow('videoseq', frame)

    def show(self, flag, frame):
        if flag is True:
            logger.info(f'exibindo o frame de id {self.frame_id}')
            self._show(frame)
        return self.control(cv2.waitKeyEx(self.__video_manager.player.delay))

    def set_commands(self, video_controller: VideoController) -> None:

        command = self.command
        command.set_command(ord('b'), PauseCommand(video_controller))
        command.set_command(ord('q'), QuitCommand(video_controller))
        command.set_command(ord('a'), RewindCommand(video_controller))
        command.set_command(ord('d'), ProceesCommand(video_controller))
        command.set_command(ord(']'), IncreaseSpeedCommand(video_controller))
        command.set_command(ord('['), DecreaseSpeedCommand(video_controller))
        command.set_command(ord(' '), PauseDelayCommand(video_controller))
        command.set_command(ord('='), RestoreDelayCommand(video_controller))
        command.set_command(ord('x'), RemoveFrameCommand(video_controller))
        command.set_command(ord('u'), UndoFrameCommand(video_controller))
        command.set_command(ord('n'), NextVideoCommand(video_controller))
        command.set_command(ord('p'), PrevVideoCommand(video_controller))

    def control(self, key):
        self.command.executor_command(key)
        return key

    def read(self):
        return self.__video_controller.read()

    def quit(self):
        return self.__video_controller.quit()
