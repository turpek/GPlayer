from pytest import fixture
from src.buffer_right import VideoBufferRight
from threading import Semaphore
# from time import sleep
from unittest.mock import patch

import cv2
import ipdb
import numpy as np
import pytest


def lote(start, end, step=1):
    return [(frame_id, np.ones((2, 2))) for frame_id in range(start, end, step)]


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
def myvideo(mycap, request):
    lote, buffersize = request.param
    cap = mycap.return_value
    semaphore = Semaphore()
    buffer = VideoBufferRight(cap, lote, semaphore, buffersize=buffersize)
    yield buffer

    buffer.join()


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_0(myvideo):
    expect = 0
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 20)), 5)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_15(myvideo):
    expect = 15
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_set_sequencia_linear(myvideo):
    expect = 75
    myvideo.set(75)
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_set_sequencia_nao_linear(myvideo):
    expect = 196
    myvideo.set(195)
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_buffer_vazio(myvideo):
    expect = 0
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_buffer_nao_vazio(myvideo):
    expect = 55
    [myvideo._buffer.put(frame) for frame in lote(54, 29, -1)]
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 500, 7)), 25)], indirect=True)
def test_buffer_VideoBufferRight_start_frame_buffer_nao_vazio_e_nao_linear(myvideo):
    expect = 392
    [myvideo._buffer.put(frame) for frame in lote(385, 215, -7)]
    result = myvideo.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(20)), 5)], indirect=True)
def test_buffer_VideoBufferRight_sequence_linear(myvideo):
    lote = list(range(0, 20))
    expect = {key for key in lote}
    result = myvideo.lot_mapping
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(150)), 25)], indirect=True)
def test_buffer_VideoBufferRight_metodo_set_frame(myvideo):
    expect_start_frame = 25
    myvideo.set(25)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_buffer_vazio_0(myvideo):
    expect = 5
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 200)), 5)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_buffer_vazio_15(myvideo):
    expect = 20
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 200)), 5)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_set_25(myvideo):
    expect = 30
    myvideo.set(25)
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_set_0(myvideo):
    expect = 5
    myvideo.set(0)
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_buffer_nao_vazio(myvideo):
    expect = 79
    [myvideo._buffer.put(frame) for frame in lote(54, 29, -1)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 25)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_com_end_frame_0(myvideo):
    expect = 49
    [myvideo._buffer.put(frame) for frame in lote(24, -1, -1)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 500, 7)), 25)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_buffer_nao_vazio_e_nao_linear_atingindo_o_limite(myvideo):
    expect = 497
    [myvideo._buffer.put(frame) for frame in lote(385, 215, -7)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 500, 7)), 5)], indirect=True)
def test_buffer_VideoBufferRight_end_frame_buffer_nao_vazio_e_nao_linear(myvideo):
    expect = 420
    [myvideo._buffer.put(frame) for frame in lote(385, 355, -7)]
    result = myvideo.end_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferRight_metodo_set_frame_com_lote_nao_linear(myvideo):
    expect_start_frame = 196
    myvideo.set(195)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(0, 212, 7)), 25)], indirect=True)
def test_buffer_VideoBufferRight_metodo_set_frame_com_lote_nao_linear_penultimo_frame(myvideo):
    expect_start_frame = 196
    myvideo.set(195)
    result_start_frame = myvideo.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_enchendo_o_buffer_manualmente(myvideo):
    expect = 10
    [myvideo._buffer.put(frame) for frame in lote(10, 0, -1)]
    result = len(myvideo)
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_done_eh_true_com_o_buffer_vazio(myvideo):
    expect = False
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_done_eh_false_com_o_buffer_cheio(myvideo):
    expect = False
    [myvideo._buffer.put(frame) for frame in lote(49, 24, -1)]
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_done_eh_true(myvideo):
    expect = True
    [myvideo._buffer.put(frame) for frame in lote(100, 74, -1)]
    result = myvideo.is_done()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_vazio_sem_set(myvideo):
    expect = True
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_vazio_set_0(myvideo):
    expect = True
    myvideo.set(0)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_vazio_set_1(myvideo):
    expect = True
    myvideo.set(1)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_vazio_com_set_50(myvideo):
    expect = True
    myvideo.set(50)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_cheio(myvideo):
    expect = True
    [myvideo._buffer.sput(frame) for frame in lote(50, 75, 1)]
    myvideo._buffer.unqueue()
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_buffer_cheio_com_frame_id_no_final(myvideo):
    expect = False
    [myvideo._buffer.sput(frame) for frame in lote(75, 100, 1)]
    myvideo._buffer.unqueue()
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_colocando_dados_manualmente(myvideo):
    expect = False
    [myvideo.put(*frame) for frame in lote(99, 74, -1)]
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_com_set_0(myvideo):
    expect = True
    myvideo.set(0)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_com_set_1(myvideo):
    expect = True
    myvideo.set(1)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_do_task_com_set_33(myvideo):
    expect = True
    myvideo.set(33)
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_task_complete_sem_set(myvideo):
    expect = False
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_task_complete_set_0(myvideo):
    expect = False
    myvideo.set(0)
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_task_complete_set_99(myvideo):
    expect = True
    myvideo.set(99)
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_task_complete_colocando_manualmente_de_30_55(myvideo):
    expect = False
    [myvideo._buffer.put(frame) for frame in lote(55, 29, -1)]
    myvideo.get()
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_is_task_complete_colocando_manualmente_de_75_99_consumindo_tudo(myvideo):
    expect = True
    [myvideo._buffer.put(frame) for frame in lote(99, 74, -1)]
    [myvideo.get() for x in range(25)]
    result = myvideo.is_task_complete()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_run_sem_set_e_vazio(myvideo):
    expect = False
    myvideo.run()
    result = myvideo.do_task()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_run_set_50(myvideo):
    expect = False
    myvideo.set(50)
    myvideo.run()
    result = myvideo._buffer.secondary_empty()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_run_2vezes_set_50(myvideo):
    expect = False
    myvideo.set(50)
    myvideo.run()

    # run é chamado dentro de get
    myvideo.get()
    result = myvideo._buffer.secondary_empty()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_put_e_run(myvideo):
    expect = False
    [myvideo.put(*frame) for frame in lote(75, 49, -1)]
    myvideo.get()
    result = myvideo._buffer.secondary_empty()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferRight_put_e_run_consumindo_tudo_com_get_checando_os_frames_id(myvideo):
    expect = list(range(50, 100, 1))
    [myvideo.put(*frame) for frame in lote(75, 49, -1)]
    result = [myvideo.get()[0] for _ in range(50)]
    assert result == expect
