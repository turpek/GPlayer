from src.buffer import VideoBufferLeft, VideoBufferRight
from src.control import Control
from tests.my_mocks import MyVideoCapture
from pytest import fixture
from unittest.mock import patch

import ipdb


@fixture
def seq1():
    SEQ1 = {
        'filename': 'video.mkv',
        'start_frame': 100,
        'end_frame': 123,
        'lot': ['0', '1', '2', '3'],
        '0': [100, 101, 102, 103, 104],
        '1': [105, 106, 107, 108, 109, 110, 111],
        '2': [112, 113, 114, 115],
        '3': [116, 117, 118, 119, 120, 121, 122, 123],
        'undo': []  # undo deve ser do tipo [(lot[str], indice[int|None], frame[list[ndarray]])]
    }
    return SEQ1


@fixture
def seq2():
    SEQ2 = {
        'filename': 'video.mkv',
        'start_frame': 100,
        'end_frame': 123,
        'lot': ['0', '1', '2', '3'],
        '0': [100, 101, 102, 103, 104],
        '1': [105, 106, 107, 108, 109, 110, 111],
        '2': [112, 113, 114, 115],
        '3': [116, 117, 118, 119, 120, 121, 122, 123],
        'undo': [
            #  1o comando: c
        ]
    }
    return SEQ2


@fixture
def seq3():
    SEQ3 = {
        'filename': 'video.mkv',
        'start_frame': 100,
        'end_frame': 123,
        'lot': ['0', '1', '2', '3', '4'],
        '0': list(range(60)),
        '1': list(range(60, 100)),
        '2': list(range(100, 142)),
        '3': list(range(142, 204)),
        '4': list(range(204, 278)),
        'undo': [
            #  1o comando: c
        ]
    }
    return SEQ3


@fixture
def mycap():
    with patch('src.control.cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock

# ################ TESTE SOBRE OS LOTES #######################


def test_control_filename(mycap, seq1):
    expect = 'video.mkv'

    control = Control(seq1)
    result = control.filename

    assert result == expect


def test_control_start_frame(mycap, seq1):
    expect = 100

    control = Control(seq1)
    result = control.start_frame

    assert result == expect


def test_control_end_frame(mycap, seq1):
    expect = 123

    control = Control(seq1)
    result = control.end_frame

    assert result == expect


def test_control_current_lot(mycap, seq1):
    expect = '0'

    control = Control(seq1)
    result = control.lot()

    assert result == expect


def test_control_next_lot(mycap, seq1):
    expect = '1'

    control = Control(seq1)
    control.next_lot()
    result = control.lot()

    assert result == expect


def test_control_next_lot_ultimo_lote(mycap, seq1):
    expect = '3'

    control = Control(seq1)
    [control.next_lot() for _ in range(3)]
    result = control.lot()

    assert result == expect


def test_control_next_lot_passando_do_ultimo_lote(mycap, seq1):
    expect = '3'

    control = Control(seq1)
    [control.next_lot() for _ in range(6)]
    result = control.lot()

    assert result == expect


def test_control_prev_lot_voltando_1_lote(mycap, seq1):
    expect = '0'

    control = Control(seq1)
    control.next_lot()
    control.prev_lot()
    result = control.lot()

    assert result == expect


def test_control_prev_lot_a_partir_do_ultimo_lote(mycap, seq1):
    expect = '2'

    control = Control(seq1)
    [control.next_lot() for _ in range(6)]
    control.prev_lot()
    result = control.lot()

    assert result == expect


def test_control_prev_lot_para_o_inicio_a_partir_do_ultmo_lote(mycap, seq1):
    expect = '0'

    control = Control(seq1)
    [control.next_lot() for _ in range(3)]
    [control.prev_lot() for _ in range(3)]
    control.prev_lot()
    result = control.lot()

    assert result == expect


def test_control_prev_lot_ultrapassando_o_inicio(mycap, seq1):
    expect = '0'

    control = Control(seq1)
    [control.next_lot() for _ in range(3)]
    [control.prev_lot() for _ in range(6)]
    control.prev_lot()
    result = control.lot()

    assert result == expect


# ######### TESTES SOBRE OS FRAMES #################################3


def test_control_frames_id_do_lote_0(mycap, seq1):
    expect = [100, 101, 102, 103, 104]

    control = Control(seq1)
    result = control.frames_id()

    assert result == expect


def test_control_frames_id_do_lote_2(mycap, seq1):
    expect = [105, 106, 107, 108, 109, 110, 111]

    control = Control(seq1)
    control.next_lot()
    result = control.frames_id()

    assert result == expect


def test_control_frames_id_do_ultimo_lote(mycap, seq1):
    expect = [116, 117, 118, 119, 120, 121, 122, 123]

    control = Control(seq1)
    [control.next_lot() for _ in range(5)]
    result = control.frames_id()

    assert result == expect


def test_control_primeiro_frame(mycap, seq1):
    expect = 100

    control = Control(seq1)
    result = control.frame_id()

    assert result == expect


def test_control_next_frame(seq3, mycap):
    expect = 1

    control = Control(seq3)
    control.next_frame()
    result = control.frame_id()

    assert result == expect


def test_control_next_frame_2(seq3, mycap):
    expect = 2

    control = Control(seq3)
    control.next_frame()
    control.next_frame()
    result = control.frame_id()

    assert result == expect


def test_control_next_frame_consumindo_o_buffer_de_25(seq3, mycap):
    expect = 25

    control = Control(seq3, buffersize=25)
    [control.next_frame() for _ in range(24)]
    control.next_frame()
    result = control.frame_id()

    assert result == expect


def test_control_next_frame_consumindo_o_buffer_de_25_e_enchendo_o_mesmo(seq3, mycap):
    expect = 26

    control = Control(seq3, buffersize=25)
    [control.next_frame() for _ in range(25)]
    control.next_frame()
    result = control.frame_id()

    assert result == expect


def test_control_prev_frame_0(seq3, mycap):
    expect = 0

    control = Control(seq3)
    control.prev_frame()
    result = control.frame_id()

    assert result == expect


def test_control_prev_frame_1(seq3, mycap):
    expect = 0

    control = Control(seq3)
    control.next_frame()
    control.prev_frame()
    result = control.frame_id()

    assert result == expect


def test_control_prev_frame_consumindo_o_buffer_de_25_e_voltando_um_frame(seq3, mycap):
    expect = 24
    expect_size_right = 1

    control = Control(seq3, buffersize=25)
    [control.next_frame() for _ in range(25)]
    control.prev_frame()
    result = control.frame_id()
    result_size_right = control.bufferRight.qsize()

    assert result == expect
    assert result_size_right == expect_size_right


def test_control_prev_frame_consumindo_o_buffer_de_25_e_voltando_todos_os_frames(seq3, mycap):
    expect = 0
    expect_size_right = 25

    control = Control(seq3, buffersize=25)
    [control.next_frame() for _ in range(25)]
    [control.prev_frame() for _ in range(25)]
    result = control.frame_id()
    result_size_right = control.bufferRight.qsize()

    assert result == expect
    assert result_size_right == expect_size_right


def test_control_prev_frame_consumindo_o_buffer_de_25_2xVezes_e_voltando_1xVez(seq3, mycap):
    expect = 24
    expect_size_right = 25

    control = Control(seq3, buffersize=25)
    [control.next_frame() for _ in range(50)]
    [control.prev_frame() for _ in range(26)]
    result = control.frame_id()
    result_size_right = control.bufferRight.qsize()

    assert result == expect
    assert result_size_right == expect_size_right


def test_control_removendo_o_1_frame(mycap, seq1):
    expect = [101, 102, 103, 104]
    expect_story = ('0', 0, 100)
    expect_index = 0

    control = Control(seq1)
    control.remove_frame()
    result = control.frames_id()
    result_story = control.story.get()
    result_index = control.index

    assert result == expect
    assert result_story == expect_story
    assert expect_index == result_index


"""
def test_control_removendo_o_ultimo_frame(seq1):
    expect = [100, 102, 103]
    expect_story = ('0', 4, 104)

    control = Control(seq1)
    control.remove_frame()
    result = control.frames_id()
    result_story = control.story.get()

    assert result == expect
    assert result_story == expect_story
"""
