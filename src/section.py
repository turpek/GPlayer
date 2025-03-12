from __future__ import annotations
from collections import deque
from loguru import logger
from queue import LifoQueue, Queue
from src.adapter import ISectionAdapter, SectionUnionAdapter
from src.custom_exceptions import SectionError, SectionIdError
from src.frame_mapper import FrameMapper
from src.trash import Trash
import bisect


class VideoSection:
    def __init__(self, adapter: ISectionAdapter):
        self.__start = adapter.start()
        self.__end = adapter.end()
        self.__removed_frame = adapter.removed_frames()
        self.black_list_frames = adapter.black_list_frames()
        self.__id = self.__calculate_id()

    def __repr__(self):
        return f"VideoSection('{self.id_}')"

    def __add__(self, obj: VideoSection) -> VideoSection:
        return VideoSection(SectionUnionAdapter(self, obj))

    def __eq__(self, obj: int | VideoSection) -> bool:
        if isinstance(obj, VideoSection):
            return self.id_ == obj.id_
        return self.id_ == obj

    def __lt__(self, obj: VideoSection) -> bool:
        return self.id_ < obj.id_

    def __calculate_id(self):
        if len(self.get_trash()) > 0:
            removed = min(self.get_trash())
            return min(self.start, removed)
        return self.start

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @property
    def id_(self):
        return self.__id

    def update_range(self, frame_map: FrameMapper):
        """Atualiza o range da seção, ou seja, o start e end dos frames"""
        self.__start = frame_map[0]
        self.__end = frame_map[-1]

    def get_trash(self) -> deque:
        """
        Devolve uma pilha dos frames removidos, portanto os elementos
        no topo do deque foram os primeiros removidos
        """
        return self.__removed_frame


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
