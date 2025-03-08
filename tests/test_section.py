import pytest
from collections import deque
from src.section import ManagerSection, VideoSection
import numpy as np

FAKES = {
    'SECTION_IDS': [1, 2, 4],
    'REMOVED_IDS': [3, 5],
    1: {'RANGE_FRAME_ID': (0, 99), 'REMOVED_FRAMES': [14, 13, 12, 11, 10]},
    2: {'RANGE_FRAME_ID': (100, 199), 'REMOVED_FRAMES': [150, 149, 148, 147, 136, 135, 134]},
    3: {'RANGE_FRAME_ID': (202, 299), 'REMOVED_FRAMES': [201, 200]},
    4: {'RANGE_FRAME_ID': (300, 395), 'REMOVED_FRAMES': [396, 397, 398, 399]},
    5: {'RANGE_FRAME_ID': (403, 497), 'REMOVED_FRAMES': [498, 401, 499, 402]},
    6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': []},
}


class MockPlayer:
    def __init__(self):
        ...


class MockTrash:
    def __init__(self):
        self._stack = deque()

    def undo(self) -> tuple[bool | np.ndarray]:
        return (True, np.zeros((2, 2)))

    def import_frames_id(self, frames_id: deque):
        while len(frames_id):
            self._stack.put(frames_id.pop())

    def export_frames_id(self, frames_id: deque):
        while len(self._stack):
            frames_id.append(self._stack.pop())


class MockFrameMapper:
    def __init__(self, frame_mapper: list):
        self.__frames_ids = sorted(frame_mapper)

    def __getitem__(self, index):
        if len(self.__frames_ids) > 0:
            return self._frame_ids[index]


def test_VideoSection_start_frame_id_1():
    expect = 0
    secion = VideoSection(FAKES[1])
    result = secion.start_frame

    assert expect == result


def test_VideoSection_end_frame_id_1():
    expect = 99
    secion = VideoSection(FAKES[1])
    result = secion.end_frame

    assert expect == result


@pytest.mark.skip(reason='despoi vejo')
def test_VideoSection_removed_frames_id_1():
    expect = deque([])
    secion = VideoSection(FAKES[1])
    result = secion.removed_frames

    assert expect == result


def test_VideoSection_set_frames_range():
    expect_start_frame = 15
    expect_end_frame = 78

    mock_mapper = list(range(15, 79))
    section = VideoSection(FAKES[1])
    section.set_range_frames(mock_mapper)
    result_start_frame = section.start_frame
    result_end_frame = section.end_frame

    assert expect_start_frame == result_start_frame
    assert expect_end_frame == result_end_frame


def test_ManagerSection_save_data():
    expect = 1
    sections = ManagerSection(FAKES)
    result = sections.current_id
    assert expect == result


def test_ManagerSection_next_section():
    expect = 2
    sections = ManagerSection(FAKES)
    sections.next_section(MockPlayer(), MockFrameMapper([]), MockTrash())
    result = sections.current_id
    assert expect == result
