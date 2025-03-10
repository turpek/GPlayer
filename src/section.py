from collections import deque
from loguru import logger
from queue import LifoQueue, Queue
from src.custom_exceptions import SectionError, SectionIdError
from src.frame_mapper import FrameMapper
from src.trash import Trash
import bisect

# Indice para fazer a leitura do dicionario da seção
SECTION_IDS = 'SECTION_IDS'
REMOVED_IDS = 'REMOVED_IDS'
START_FRAME = 0  # Indice para a leitura da tupla do range de frames
END_FRAME = 1  # Indice para a leitura da tupla do range de frames
RANGE_FRAMES = 'RANGE_FRAME_ID'
REMOVED_FRAMES = 'REMOVED_FRAMES'


class VideoSection:
    def __init__(self, section: dict):
        self.start_frame = section[RANGE_FRAMES][START_FRAME]
        self.end_frame = section[RANGE_FRAMES][END_FRAME]
        self.removed_frames = deque(section[REMOVED_FRAMES])

    def set_range_frames(self, frame_mapper: FrameMapper):
        self.start_frame = frame_mapper[0]
        self.end_frame = frame_mapper[-1]

    def get_deque(self) -> deque:
        # self.removed_frames = deque()
        return self.removed_frames


class SectionManager:
    def __init__(self, data: dict):

        removed_ids = data[REMOVED_IDS].copy()
        self._removed_ids = deque()
        while len(removed_ids) > 0:
            self._removed_ids.append(removed_ids.pop())

        self._right = deque(sorted(data[SECTION_IDS]))
        self._left = deque()
        self._sections = dict()
        self.__load_sections(data)
        self._section: VideoSection = self.current

    def __load_sections(self, data):
        sections_id = data[SECTION_IDS] + data[REMOVED_IDS]

        if len(sections_id) == 0:
            raise SectionIdError('there are no sections id to work with')

        try:
            for sid in sections_id:
                self._sections[sid] = VideoSection(data[sid])
        except KeyError:
            raise SectionError(f"there is no data for section with id '{sid}'")

    @property
    def section_id(self):
        if len(self._right) > 0:
            return self._right[0]

    @property
    def current(self) -> VideoSection:
        if self.section_id is not None:
            return self._sections[self.section_id]

    def export_frames_id(self, trash: Trash):
        """Exporta os frames id excluídos para uma possível restauração futura."""
        trash.export_frames_id(self.current.get_deque())

    def save_data(self, frame_mapper: FrameMapper, trash: Trash):
        """Salva os dados """
        self.current.set_range_frames(frame_mapper)
        self.export_frames_id(trash)

    def next_section(self):
        if len(self._right) > 1:
            self._left.append(self._right.popleft())

    def prev_section(self):
        if len(self._left) > 0:
            self._right.appendleft(self._left.pop())

    def __restore_section_right(self, section_id):
        bisect.insort_right(self._right, section_id)
        while self.section_id != section_id:
            self.next_section()

    def __restore_section_left(self, section_id):
        bisect.insort_right(self._left, section_id)
        while self.section_id != section_id:
            self.prev_section()

    def restore_section(self):
        if len(self._removed_ids) == 0:
            logger.debug('there are no sections to restore')
            return False

        section_id = self._removed_ids.pop()
        if len(self._right) == 0:
            self._right.appendleft(section_id)
        elif section_id < self.section_id:
            self.__restore_section_left(section_id)
        else:
            self.__restore_section_right(section_id)
        return True

    def remove_section(self):
        if len(self._right) > 1:
            self._right.popleft()
        elif len(self._right) > 0:
            self._right.popleft()
            self.prev_section()

    def section_range(self) -> tuple[int, int]:
        return (self.current.start_frame, self.current.end_frame)

    def section_removed(self) -> list[int]:
        return list(self.current.removed_frames)

    @property
    def removed_ids(self) -> list[int]:
        return list(self._removed_ids)
