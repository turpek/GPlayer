from collections import deque
from src.custom_exceptions import SimpleStackError
from src.utils import SimpleStack, SectionMementoHandler
from src.memento import Caretaker, TrashOriginator
from src.section import VideoSection
from src.adapter import FakeSectionAdapter
from pytest import fixture, raises
import numpy as np

FAKES = {
    'SECTION_IDS': [1, 2, 4],
    'REMOVED_IDS': [5, 3, 6],
    1: {'RANGE_FRAME_ID': (0, 99), 'REMOVED_FRAMES': [14, 13, 12, 11, 10], 'BLACK_LIST': []},
    2: {'RANGE_FRAME_ID': (100, 199), 'REMOVED_FRAMES': [150, 149, 148, 147, 136, 135, 134], 'BLACK_LIST': []},
    3: {'RANGE_FRAME_ID': (202, 299), 'REMOVED_FRAMES': [200], 'BLACK_LIST': [210, 211, 212, 213, 214, 215]},
    4: {'RANGE_FRAME_ID': (300, 395), 'REMOVED_FRAMES': [398, 399], 'BLACK_LIST': []},
    5: {'RANGE_FRAME_ID': (403, 497), 'REMOVED_FRAMES': [498, 401, 499, 402], 'BLACK_LIST': [400]},
    6: {'RANGE_FRAME_ID': (500, 599), 'REMOVED_FRAMES': [], 'BLACK_LIST': []},
}


class MockFrameMapper:
    def __init__(self, frame_mapper: list):
        self.__frame_ids = sorted(frame_mapper)

    def __getitem__(self, index):
        if len(self.__frame_ids) > 0:
            return self.__frame_ids[index]

    def add(self, value):
        import bisect
        bisect.insort_left(self.__frame_ids, value)


@fixture
def sections():
    list_sections = [VideoSection(FakeSectionAdapter(FAKES[k])) for k in [1, 2, 3, 4, 5, 6]]
    yield list_sections


def test_SimpleStack_top_sem_push():
    expect = None
    stack = SimpleStack(int)
    result = stack.top()
    assert expect == result


def test_SimpleStack_top_com_1x_push():
    expect = 1
    stack = SimpleStack(int)
    stack.push(1)
    result = stack.top()
    assert expect == result


def test_SimpleStack_top_com_2x_push():
    expect = 2
    stack = SimpleStack(int)
    stack.push(1)
    stack.push(2)
    result = stack.top()
    assert expect == result


def test_SimpleStack_pop_sem_push():
    expect = "Pop failed: Stack is empty."
    stack = SimpleStack(int)
    with raises(SimpleStackError) as excinfo:
        stack.pop()
    result = f'{excinfo.value}'
    assert expect == result


def test_SimpleStack_pop_1x_push():
    expect = 1
    stack = SimpleStack(int)
    stack.push(1)
    result = stack.pop()
    assert expect == result


def test_SimpleStack_pop_2x_push():
    expect = 2
    stack = SimpleStack(int)
    stack.push(1)
    stack.push(2)
    result = stack.pop()
    assert expect == result


def test_SimpleStack_empty_fila_vazia():
    stack = SimpleStack(int)
    assert stack.empty()


def test_SimpleStack_empty_fila_nao_vazia():
    stack = SimpleStack(int)
    stack.push(1)
    assert not stack.empty()


def test_SimpleStack_empty_fila_vazia_apos_push_e_pop():
    stack = SimpleStack(int)
    stack.push(1)
    stack.pop()
    assert stack.empty()


def test_SimplesStack_push_elemento_de_mesmo_tipo():
    stack = SimpleStack(int)
    stack.push(1)


def test_SimplesStack_push_elemento_de_tipo_diferente():
    expect = 'Expected type "int", but received "str".'
    with raises(TypeError) as excinfo:
        stack = SimpleStack(int)
        stack.push('1')
    result = str(excinfo.value)
    assert expect == result


# ############ Testes para a classe SectionMementoHandler ##################

def test_SectionMementoHandler_exportar_dados_para_seção_sem_frames_removidos(sections):
    expect = deque()
    section = sections[5]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.store_mementos(section)
    result = section.get_trash()
    assert expect == result


def test_SectionMementoHandler_exportar_dados_com_1_elemento(sections):
    expect = deque([500])
    section = sections[5]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    originator.set_state(500)
    caretaker.save(originator)
    handler = SectionMementoHandler(originator, caretaker)
    handler.store_mementos(section)
    result = section.get_trash()
    assert expect == result


def test_SectionMementoHandler_exportar_dados_com_5_elemento(sections):
    frames_id = [503, 505, 502, 501, 504, 500]
    expect = deque(frames_id)
    section = sections[5]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    for frame_id in frames_id[::-1]:
        originator.set_state(frame_id)
        caretaker.save(originator)
    handler = SectionMementoHandler(originator, caretaker)
    handler.store_mementos(section)
    result = section.get_trash()
    assert expect == result


def test_SectionMementoHandler_importar_dados_de_memento_vazio(sections):
    section = sections[5]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.load_mementos(section)
    assert not caretaker.can_undo()


def test_SectionMementoHandler_importar_dados_de_memento_1_elemento(sections):
    expect = 200
    section = sections[2]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.load_mementos(section)
    assert caretaker.can_undo()

    caretaker.undo(originator)
    result = originator.get_state()
    assert expect == result


def test_SectionMementoHandler_importar_dados_de_memento_2_elemento(sections):
    expect = 399
    section = sections[3]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.load_mementos(section)

    caretaker.undo(originator)
    caretaker.undo(originator)
    originator.get_state()
    result = originator.get_state()
    assert expect == result


def test_SectionMementoHandler_importar_e_exportar_dados(sections):
    expect = deque([150, 149, 148, 147, 136, 135, 134])
    section = sections[1]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.load_mementos(section)
    handler.store_mementos(section)
    result = section.get_trash()
    assert expect == result


def test_SectionMementoHandler_importar_remove_e_exporta_dados(sections):
    expect = deque([199, 150, 149, 148, 147, 136, 135, 134])
    section = sections[1]  # Essa seção não tem frames removidos
    caretaker = Caretaker()
    originator = TrashOriginator(MockFrameMapper([]))
    handler = SectionMementoHandler(originator, caretaker)
    handler.load_mementos(section)

    originator.set_state(199)
    caretaker.save(originator)

    handler.store_mementos(section)
    result = section.get_trash()
    assert expect == result
