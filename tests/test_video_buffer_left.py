from pytest import fixture
from src.buffer_left import VideoBufferLeft
from unittest.mock import patch
from time import sleep
from threading import Semaphore


import cv2
import ipdb
import numpy as np
import pytest

FILE = 'model.mp4'


def lote(start, end, step=1):
    return [(frame_id, np.ones((2, 2))) for frame_id in range(start, end, step)]


def consumidor(buffer):
    frames_id = list()
    while not buffer.empty():
        frame_id, _ = buffer.read()
        frames_id.append(frame_id)
    return frames_id


class MyVideoCapture():
    def __init__(self):
        self.frames = [np.zeros((2, 2)) for x in range(300)]
        self.index = 0
        self.isopened = True

    def read(self):
        if self.index < len(self.frames):
            frame = self.frames[self.index]
            self.index += 1
            return True, frame
        return False, None

    def set(self, flag, value):
        if cv2.CAP_PROP_POS_FRAMES == flag:
            if len(self.frames) >= value and value >= 0:
                self.index = value
                return True
            else:
                return False
        return False

    def get(self, flag):
        if cv2.CAP_PROP_FRAME_COUNT == flag:
            return len(self.frames)
        elif cv2.CAP_PROP_POS_FRAMES == flag:
            return self.index
        return False

    def isOpened(self):
        return self.isopened

    def release(self):
        ...


@fixture
def mycap():
    with patch('cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock


@fixture
def seq():
    sequence = [(frame_id, np.zeros((2, 2))) for frame_id in range(10)]
    return sequence


@fixture
def seq_60():
    sequence = [(frame_id, np.zeros((2, 2))) for frame_id in range(60, 65)]
    return sequence


@fixture
def myvideo(mycap, request):
    lote, buffersize = request.param
    cap = mycap.return_value
    semaphore = Semaphore()
    buffer = VideoBufferLeft(cap, lote, semaphore, bufferlog=False, buffersize=buffersize)
    return buffer


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_0(myvideo):
    expect = 0
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 20)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_15(myvideo):
    expect = 15
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_set_sequencia_linear(myvideo):
    expect = 50
    myvideo.set(75)
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_set_sequencia_nao_linear(myvideo):
    expect = 21
    myvideo.set(195)
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_buffer_vazio(myvideo):
    expect = 0
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_buffer_nao_vazio(myvideo):
    expect = 5
    [myvideo._buffer.put(frame) for frame in lote(30, 55, 1)]
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 500, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_buffer_nao_vazio_e_nao_linear(myvideo):
    expect = 35
    [myvideo._buffer.put(frame) for frame in lote(210, 383, 7)]
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(20)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_sequence_linear(myvideo):
    lote = list(range(0, 20))
    expect = {key for key in lote}
    result = myvideo.lot_mapping
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(150)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame(myvideo):
    expect_start_frame = 0
    myvideo.set(25)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_buffer_vazio_0(myvideo):
    expect = 0
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_buffer_vazio_15(myvideo):
    expect = 15
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_set_25(myvideo):
    expect = 25
    myvideo.set(25)
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_set_0(myvideo):
    expect = 0
    myvideo.set(0)
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_buffer_nao_vazio(myvideo):
    expect = 29
    [myvideo._buffer.put(frame) for frame in lote(30, 55, 1)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_com_end_frame_0(myvideo):
    expect = 0
    [myvideo._buffer.put(frame) for frame in lote(0, 25, 1)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 500, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_end_frame_buffer_nao_vazio_e_nao_linear(myvideo):
    expect = 203
    [myvideo._buffer.put(frame) for frame in lote(210, 383, 7)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame_com_lote_nao_linear(myvideo):
    expect_start_frame = 21
    myvideo.set(195)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame_com_lote_nao_linear_penultimo_frame(myvideo):
    expect_start_frame = 21
    myvideo.set(195)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_enchendo_o_buffer_manualmente(myvideo, seq):
    expect = 10
    [myvideo.put(*seq.pop(0)) for _ in range(10)]
    result = len(myvideo)
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_done_eh_true_com_o_buffer_vazio(myvideo, seq):
    expect = True
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_done_eh_false_com_o_buffer_cheio(myvideo, seq):
    expect = False
    [myvideo._buffer.put(frame) for frame in lote(25, 50, 1)]
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_done_eh_true(myvideo, seq):
    expect = True
    [myvideo._buffer.put(frame) for frame in lote(0, 25, 1)]
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_vazio_sem_set(myvideo, seq):
    expect = False
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_vazio_set_0(myvideo, seq):
    expect = False
    myvideo.set(0)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_vazio_set_1(myvideo, seq):
    expect = True
    myvideo.set(1)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_vazio_com_set_50(myvideo, seq):
    expect = True
    myvideo.set(50)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_cheio(myvideo, seq):
    expect = True
    [myvideo._buffer.sput(frame) for frame in lote(50, 75, 1)]
    myvideo._buffer.unqueue()
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_buffer_cheio_com_frame_id_no_final(myvideo, seq):
    expect = False
    [myvideo._buffer.sput(frame) for frame in lote(0, 15, 1)]
    myvideo._buffer.unqueue()
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_colocando_dados_manualmente(myvideo, seq):
    expect = False
    [myvideo.put(*frame) for frame in lote(5, 15, 1)]
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_com_set_0(myvideo, seq):
    expect = False
    myvideo.set(0)
    result = myvideo.do_task()
    # ipdb.set_trace()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_com_set_1(myvideo, seq):
    expect = True
    myvideo.set(1)
    result = myvideo.do_task()
    # ipdb.set_trace()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_do_task_com_set_33(myvideo, seq):
    expect = True
    myvideo.set(33)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_task_complete_sem_set(myvideo, seq):
    expect = True
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_task_complete_set_0(myvideo, seq):
    expect = True
    myvideo.set(0)
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_task_complete_colocando_manualmente_de_30_55(myvideo, seq):
    expect = False
    [myvideo._buffer.put(frame) for frame in lote(30, 55, 1)]
    myvideo.get()
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_is_task_complete_colocando_manualmente_de_0_25_consumindo_tudo(myvideo, seq):
    expect = True
    [myvideo._buffer.put(frame) for frame in lote(0, 25, 1)]
    [myvideo.get() for x in range(25)]
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_run_sem_set_e_vazio(myvideo, seq):
    expect = True
    myvideo.run()
    result = myvideo._buffer.empty()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_run_set_50(myvideo, seq):
    expect = False
    myvideo.set(50)
    myvideo.run()
    sleep(0.001)
    result = myvideo._buffer.secondary_empty()
    myvideo.join()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_run_2vezes_set_50(myvideo, seq):
    expect = False
    myvideo.set(50)
    myvideo.run()
    myvideo.get()
    result = myvideo._buffer.secondary_empty()
    myvideo.join()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_put_e_run(myvideo, seq):
    expect = False
    [myvideo.put(*frame) for frame in lote(50, 75, 1)]
    myvideo.get()
    result = myvideo._buffer.secondary_empty()
    myvideo.join()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_put_e_run_consumindo_tudo_com_get_checando_os_frames_id(myvideo, seq):
    expect = list(range(74, -1, -1))
    [myvideo.put(*frame) for frame in lote(50, 75, 1)]
    result = [myvideo.get()[0] for _ in range(75)]
    myvideo.join()
    assert result == expect
