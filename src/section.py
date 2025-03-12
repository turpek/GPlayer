from __future__ import annotations
from collections import deque
# from loguru import logger
from src.adapter import ISectionAdapter, ISectionManagerAdapter, SectionUnionAdapter
from src.custom_exceptions import SectionManagerError
from src.frame_mapper import FrameMapper
from src.memento import Caretaker, SectionOriginator
from src.utils import SimpleStack
# from src.trash import Trash


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


class SectionWrapper:
    def __init__(self, section_1: VideoSection, section_2: VideoSection = None):
        self.__check_section(section_1)
        if section_2 is not None:
            self.__check_section(section_2)

        self.__lower = section_1
        self.__upper = section_2
        if isinstance(section_2, VideoSection) and section_2 < section_1:
            self.__lower = section_2
            self.__upper = section_1

    def __check_section(self, section):
        if not isinstance(section, VideoSection):
            raise TypeError(f' section expected "{VideoSection.__nama__}" but received "{section.__name__}"!')

    @property
    def section_1(self) -> VideoSection:
        return self.__lower

    @property
    def section_2(self) -> VideoSection | None:
        return self.__upper


class SectionManager:
    def __init__(
        self,
        manager_adapter: ISectionManagerAdapter,
        section_adapter: ISectionAdapter
    ):
        self._right = SimpleStack(VideoSection)
        self._left = SimpleStack(VideoSection)
        self.removed_sections = SimpleStack(SectionWrapper)

        self._caretaker = Caretaker()
        self._originator = SectionOriginator()

        # O ISectionManagerAdapter deve retorna uma lista ordenada, além disso
        # devemos considerar está lista como uma "pilha", portando a remoção
        # deve ser feita no topo!
        datas = manager_adapter.get_sections()
        while len(datas):
            self._right.push(VideoSection(section_adapter(datas.pop())))

        self.__load_removed_sections(manager_adapter, section_adapter)

        if self._right.empty() and self.removed_sections.empty():
            raise SectionManagerError('there are no sections id to work with')

    def __load_removed_sections(
        self,
        manager_adapter: ISectionManagerAdapter,
        section_adapter: ISectionAdapter
    ) -> None:

        # Devemos considerar a lista retornada pelo removed_sections como uma pilha,
        # portanto a remoção deve ser feita no topo, além disso a lista deve seguir o
        # seguinte padrão list[VideoSection, VideoSection | None]
        rdatas = manager_adapter.removed_sections()
        while len(rdatas):
            section_1, section_2 = rdatas.pop()
            data = (VideoSection(section_adapter(section_1)), section_2)
            if section_2 is not None:
                data[1] = VideoSection(section_adapter(section_2))
            self.removed_sections.push(SectionWrapper(*data))

    @property
    def section_id(self) -> int:
        return self._right.top.id_

    def __next_section(self, min_size: int) -> None:
        if len(self._right) > min_size:
            self._left.push(self._right.pop())

    def next_section(self) -> None:
        """Passa para a próxima seção se existir."""

        # Como a seção atual está sempre no topo da pilha não
        # podemos remover a última seção da mesma, pois ficariamos
        # sem seção para consultar
        self.__next_section(1)

    def prev_section(self) -> None:
        """Retorna para a seção anterior."""
        if not self._left.empty():
            self._right.push(self._left.pop())

    def remove_section(self) -> None:
        ...
