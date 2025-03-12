from __future__ import annotations
from collections import deque
from src.interfaces import ISectionAdapter, ISectionManagerAdapter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.section import Section


class SectionUnionAdapter(ISectionAdapter):
    def __init__(self, section_1, section_2):

        lower, upper = self.__get_sections(section_1, section_2)

        self.__start = lower.start
        self.__end = upper.end
        self.__removed_frames = lower.get_trash() + upper.get_trash()
        self.__black_list = self.__get_black_list(lower, upper)

    def __get_sections(self, section_1, section_2):
        if section_2.id_ > section_1.id_:
            return section_1, section_2
        return section_2, section_1

    def __get_true_end(self, section):
        if len(section.get_trash()) > 0:
            end = max(section.get_trash())
            return max(section.end, end)

    def __get_black_list(self, lower, upper):
        neighbor_start = self.__get_true_end(lower) + 1
        neighbor_end = upper.id_
        neighborhood = list(range(neighbor_start, neighbor_end))
        return lower.black_list_frames + neighborhood + upper.black_list_frames

    def start(self) -> int:
        return self.__start

    def end(self) -> int:
        return self.__end

    def removed_frames(self) -> deque:
        return self.__removed_frames

    def black_list_frames(self) -> list:
        return self.__black_list


class FakeSectionAdapter(ISectionAdapter):
    def __init__(self, data):
        start, end = data['RANGE_FRAME_ID']
        self.__start = start
        self.__end = end
        self.__removed_frames = deque(data['REMOVED_FRAMES'])
        self.__black_list = data['BLACK_LIST']

    def start(self) -> int:
        return self.__start

    def end(self) -> int:
        return self.__end

    def removed_frames(self) -> deque:
        return self.__removed_frames

    def black_list_frames(self) -> list:
        return self.__black_list


class FakeSectionManagerAdapter(ISectionManagerAdapter):
    def __init__(self, data):
        self._sections = [s for s in data['SECTIONS']]
        self._removed_sections = [r for r in data['REMOVED']]

    def get_sections(self) -> list:
        return self._sections

    def removed_sections(self) -> list:
        return self._removed_sections
