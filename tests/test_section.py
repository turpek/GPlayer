import pytest
from collections import deque
from src.section import SectionManager, VideoSection
from src.custom_exceptions import SectionError, SectionIdError
from pytest import fixture
import numpy as np

FAKES = {
    'SECTION_IDS': [1, 2, 4],
    'REMOVED_IDS': [5, 3, 6],
    1: {'RANGE_FRAME_ID': (0, 99), 'REMOVED_FRAMES': [14, 13, 12, 11, 10]},
    2: {'RANGE_FRAME_ID': (100, 199), 'REMOVED_FRAMES': [150, 149, 148, 147, 136, 135, 134]},
    3: {'RANGE_FRAME_ID': (202, 299), 'REMOVED_FRAMES': [201, 200]},
    4: {'RANGE_FRAME_ID': (300, 395), 'REMOVED_FRAMES': [396, 397, 398, 399]},
    5: {'RANGE_FRAME_ID': (403, 497), 'REMOVED_FRAMES': [498, 401, 499, 402]},
    6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': []},
}


FAKES_SEM_REMOVIDOS = {
    'SECTION_IDS': [1, 2],
    'REMOVED_IDS': [],
    1: {'RANGE_FRAME_ID': (0, 99), 'REMOVED_FRAMES': [14, 13, 12, 11, 10]},
    2: {'RANGE_FRAME_ID': (100, 199), 'REMOVED_FRAMES': [150, 149, 148, 147, 136, 135, 134]},
}


class MockPlayer:
    def __init__(self):
        ...


class MockTrash:
    def __init__(self):
        self._stack = deque()

    def _set_data(self, dados: deque()):
        self._stack = dados.copy()

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
        self.__frame_ids = sorted(frame_mapper)

    def __getitem__(self, index):
        if len(self.__frame_ids) > 0:
            return self.__frame_ids[index]


def gera_mock(frames_mapping, removed):
    frame_mapping = sorted(set(frames_mapping) - set(removed))
    mapping = MockFrameMapper(frame_mapping)
    trash = MockTrash()
    trash._set_data(deque(removed))
    return mapping, trash


def gera_mock_com_fake(index):
    start, end = FAKES[index]['RANGE_FRAME_ID']
    frame_mapping = list(range(start, end + 1))
    removed = FAKES[index]['REMOVED_FRAMES']
    return gera_mock(frame_mapping, removed)


@fixture
def sections():
    section_manager = SectionManager(FAKES)
    yield section_manager


@fixture
def mock_config(request):
    frames_mapping, removed = request.param
    mapping, trash = gera_mock(frames_mapping, removed)
    yield mapping, trash


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


def test_VideoSection_removed_frames_id_1():
    expect = deque([14, 13, 12, 11, 10])
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


def test_SectionManager_com_dados_vazios_mas_sem_id():
    expect = 'there are no sections id to work with'
    with pytest.raises(SectionIdError) as excinfo:
        data = {'SECTION_IDS': [], 'REMOVED_IDS': []}
        SectionManager(data)
    result = f'{excinfo.value}'
    assert expect == result


def test_SectionManager_com_dados_vazios_mas_com_id():
    sid = 6
    expect = f"there is no data for section with id '{sid}'"
    with pytest.raises(SectionError) as excinfo:
        data = {'SECTION_IDS': [sid], 'REMOVED_IDS': []}
        SectionManager(data)
    result = f'{excinfo.value}'
    assert expect == result


def test_SectionManager_com_dados_vazios_mas_com_id_para_restaurar():
    sid = 6
    expect = f"there is no data for section with id '{sid}'"
    with pytest.raises(SectionError) as excinfo:
        data = {'SECTION_IDS': [], 'REMOVED_IDS': [sid]}
        SectionManager(data)
    result = f'{excinfo.value}'
    assert expect == result


@pytest.mark.parametrize('mock_config', [(list(range(100)), [0, 1, 2, 3, 4, 5])], indirect=True)
def test_SectionManager_save_data_removendo_os_5_primeiros_frames(sections, mock_config):
    mapping, trash = mock_config
    expect_range = (6, 99)
    expect_removed = [5, 4, 3, 2, 1, 0]

    sections.save_data(mapping, trash)
    result_range = sections.section_range()
    result_removed = sections.section_removed()

    assert expect_range == result_range
    assert expect_removed == result_removed


@pytest.mark.parametrize('mock_config', [(list(range(100, 200)), [134, 135, 136, 148, 149, 150])], indirect=True)
def test_SectionManager_save_data_restaurando_tudo(sections, mock_config):
    mapping, trash = mock_config
    expect = []

    trash = MockTrash()
    trash._set_data(deque())
    sections.save_data(mapping, trash)
    result = sections.section_removed()

    assert expect == result


@pytest.mark.parametrize('mock_config', [(list(range(200, 300)), [200, 201])], indirect=True)
def test_SectionManager_save_data_restaurando_o_1o_e_removendo_o_ultimo(sections, mock_config):
    mapping, trash = mock_config
    expect_range = (200, 298)
    expect_removed = [299]

    trash = MockTrash()
    trash._set_data(deque([299]))
    mapping = MockFrameMapper(list(range(200, 299)))
    sections.save_data(mapping, trash)
    result_range = sections.section_range()
    result_removed = sections.section_removed()

    assert expect_range == result_range
    assert expect_removed == result_removed


@pytest.mark.parametrize('mock_config', [(list(range(300, 396)), [396, 397, 398, 399])], indirect=True)
def test_SectionManager_save_data_restaurando_os_ultimos_e_removendo_o_1o(sections, mock_config):
    mapping, trash = mock_config
    expect_range = (301, 399)
    expect_removed = [300]

    trash = MockTrash()
    trash._set_data(deque([300]))
    mapping = MockFrameMapper(list(range(301, 400)))
    sections.save_data(mapping, trash)
    result_range = sections.section_range()
    result_removed = sections.section_removed()

    assert expect_range == result_range
    assert expect_removed == result_removed


def test_SectionManager_next_section_1x():
    expect = 2
    expect_range = (100, 199)

    sections = SectionManager(FAKES)
    sections.next_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_next_section_2x():
    expect = 4
    expect_range = (300, 395)

    sections = SectionManager(FAKES)
    for _ in range(2):
        sections.next_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_prev_section_no_inicio():
    expect = 1
    expect_range = (0, 99)

    sections = SectionManager(FAKES)
    sections.prev_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_next_section_no_final_1x():
    expect = 2
    expect_range = (100, 199)
    sections = SectionManager(FAKES)

    for _ in range(2):
        sections.next_section()
    sections.prev_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_next_section_no_final_2x():
    expect = 1
    expect_range = (0, 99)
    sections = SectionManager(FAKES)

    for _ in range(2):
        sections.next_section()
    for _ in range(2):
        sections.prev_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_next_section_no_final_3x():
    expect = 1
    expect_range = (0, 99)
    sections = SectionManager(FAKES)

    for _ in range(2):
        sections.next_section()
    for _ in range(2):
        sections.prev_section()

    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_sem_nenhuma_secao_excluida():
    expect = 1

    sections = SectionManager(FAKES_SEM_REMOVIDOS)
    sections.restore_section()
    result = sections.section_id
    assert expect == result


def test_SectionManager_restore_section_sem_nenhuma_secao_1x():
    expect = 6
    expect_range = (500, 599)

    data = {
        'SECTION_IDS': [], 'REMOVED_IDS': [6],
        6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': []}
    }

    sections = SectionManager(data)
    sections.restore_section()
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_1x():
    expect = 5
    expect_range = (403, 497)

    sections = SectionManager(FAKES)
    sections.restore_section()
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_2x():
    expect = 3
    expect_range = (202, 299)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(2)]
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_sem_nenhuma_secao_2x():
    expect = 3
    expect_range = (202, 299)

    data = {
        'SECTION_IDS': [], 'REMOVED_IDS': [6, 3],
        6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': []},
        3: {'RANGE_FRAME_ID': (202, 299), 'REMOVED_FRAMES': [201, 200]},
    }

    sections = SectionManager(data)
    [sections.restore_section() for _ in range(2)]
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_3x():
    expect = 6
    expect_range = (500, 599)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(3)]
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_2x_next_1x():
    expect = 4
    expect_range = (300, 395)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(2)]
    sections.next_section()
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_2x_prev_1x():
    expect = 2
    expect_range = (100, 199)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(2)]
    sections.prev_section()
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_3x_next_1x():
    expect = 6
    expect_range = (500, 599)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(3)]
    sections.next_section()
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_3x_prev_2x():
    expect = 4
    expect_range = (300, 395)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(3)]
    [sections.prev_section() for _ in range(2)]
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_restore_section_3x_prev_5x():
    expect = 1
    expect_range = (0, 99)

    sections = SectionManager(FAKES)
    [sections.restore_section() for _ in range(3)]
    [sections.prev_section() for _ in range(5)]
    result = sections.section_id
    result_range = sections.section_range()

    assert expect == result
    assert expect_range == result_range


def test_SectionManager_remove_section_vazia():
    expect = None

    data = {
        'SECTION_IDS': [], 'REMOVED_IDS': [6, 3],
        6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': []},
        3: {'RANGE_FRAME_ID': (202, 299), 'REMOVED_FRAMES': [201, 200]},
    }
    sections = SectionManager(data)
    sections.remove_section()
    result = sections.section_id

    assert expect == result


def test_SectionManager_remove_section():
    expect = 2

    sections = SectionManager(FAKES)
    sections.remove_section()
    result = sections.section_id

    assert expect == result


def test_SectionManager_remove_section_ultimo_secao():
    expect = 2

    sections = SectionManager(FAKES)
    [sections.next_section() for _ in range(2)]
    sections.remove_section()
    result = sections.section_id

    assert expect == result
