import cv2

from array import array
from collections import deque
from threading import Semaphore

from src.buffer_left import VideoBufferLeft
from src.buffer_right import VideoBufferRight
from src.frame_mapper import FrameMapper
from src.section import SectionManager
from src.player_control import PlayerControl
from src.trash import Trash
from src.utils import VideoInfo


class VideoManager:

    def __init__(self, buffersize, log):
        self.__log = log
        self.__buffersize = buffersize
        self.mapping = None
        self.path = None
        self.frame_count = None
        self.semaphore = Semaphore()
        self.player = PlayerControl()
        self.__section_manager = None

    def set_mapping(self, frame_ids: list = None) -> None:
        """
        Define o mapping de frames que serão lidos e armazenados no buffer.

        Returns:
            None
        """

        frame_count = self.frame_count
        if not isinstance(frame_ids, (list, tuple, array)):
            frame_ids = list(range(frame_count))

        if isinstance(self.mapping, FrameMapper):
            self.mapping.set_mapping(frame_ids, frame_count, [])
            return self.mapping
        else:
            return FrameMapper(frame_ids, frame_count)

    def load_capture(self, video_info: VideoInfo):
        self.path = video_info.path
        self.__cap = cv2.VideoCapture(str(self.path))
        video_info.load_video_property(self.__cap)
        self.frame_count = video_info.frame_count

    def load_mapping(self, section_manager: SectionManager):
        self.mapping = self.set_mapping(section_manager.get_mapping())

    def load_trash(self, section_manager: SectionManager):
        self.trash = Trash(self.__cap,
                           self.semaphore,
                           self.frame_count,
                           buffersize=20)
        section_manager.load_mementos_frames(self.trash)

    def load_player(self, servant: VideoBufferRight, master: VideoBufferLeft):
        self.player.set_buffers(servant, master)

    def load_buffers(self):
        args = (self.__cap,
                self.mapping,
                self.semaphore)

        bsize, log = self.__buffersize, self.__log
        self.servant = VideoBufferRight(*args, buffersize=bsize, bufferlog=log)
        self.master = VideoBufferLeft(*args, buffersize=bsize, bufferlog=log)
        self.load_player(self.servant, self.master)

    def create(self, frames_mapping: list[int] | None, removed_frames: deque):

        # Removendo os frames excluidos do mapping
        if isinstance(frames_mapping, (list, tuple, array)):
            frames_mapping = set(frames_mapping) - set(removed_frames)

        self.player.servant.join_like()
        self.player.master.join_like()
        self.load_mapping(list(frames_mapping))
        self.load_buffers()
        self.trash.reset(self.frame_count)
        self.trash.import_frames_id(removed_frames)

    def open(self, video_info: VideoInfo):
        self.load_capture(video_info)
        self.load_mapping(video_info)
        self.load_trash()
        self.load_buffers()

        # Iniciando a task e esperando que a mesma esteja concluida.
        self.servant.run()
        self.servant._buffer.wait_task()

    def get(self):
        return (self.player,
                self.mapping,
                self.trash)
