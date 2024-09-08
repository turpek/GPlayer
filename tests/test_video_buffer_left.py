from pytest import fixture
from src.buffer_left import VideoBufferLeft
from unittest.mock import patch
from threading import Semaphore


import cv2
import ipdb
import numpy as np
import pytest

FILE = 'model.mp4'


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
    buffer = VideoBufferLeft(cap, lote, semaphore, buffersize=buffersize)
    return buffer



@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_0(myvideo):
    expect = 0
    buffer = myvideo
    result = buffer.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(15, 20)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_start_frame_15(myvideo):
    expect = 15
    buffer = myvideo
    result = buffer.start_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(20)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_sequence_linear(myvideo):
    lote = list(range(0, 20))
    expect = {key for key in lote}
    buffer = myvideo
    result = buffer.lot_mapping
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(150)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame(myvideo):
    expect_start_frame = 0
    buffer = myvideo
    buffer.set(25)
    buffer._checkout()
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame_com_lote_nao_linear(myvideo):
    expect_start_frame = 0
    buffer = myvideo
    buffer.set(25)
    buffer._checkout()
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(0, 200, 7)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_metodo_set_frame_com_lote_nao_linear_penultimo_frame(myvideo):
    expect_start_frame = 21
    buffer = myvideo
    buffer.set(195)
    buffer._checkout()
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_enchendo_o_buffer_manualmente(myvideo, seq):
    expect_start_frame = False
    expect_qsize = 10
    buffer = myvideo
    [buffer.put(*seq.pop(0)) for _ in range(10)]
    result_start_frame = buffer.start_frame()
    result_qsize = buffer.qsize()
    assert result_start_frame == expect_start_frame
    assert result_qsize == expect_qsize


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_enchendo_o_buffer_manualmente_com_o_buffer_lotado(myvideo, seq_60):
    expect_start_frame = False
    buffer = myvideo
    buffer.bufferlog = True
    [buffer.queue.append((frame_id, np.zeros((2, 2)))) for frame_id in range(25, 50)]
    buffer._old_frame = 25
    buffer._frame_id = 50
    [buffer.put(*seq_60.pop(0)) for _ in range(3)]
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame

    # Consumindo os frames para testar se start_frame() deixa de estar bloqueado
    expect_start_frame = 2
    [buffer.read() for _ in range(25)]
    try:
        buffer.read()
    except TimeoutError:
        ...
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


@pytest.mark.parametrize('myvideo', [(list(range(100)), 25)], indirect=True)
def test_buffer_VideoBufferLeft_lendo_todo_o_video(myvideo, seq):
    expect = 99
    buffer = myvideo
    buffer.bufferlog = True
    buffer.set(99)
    buffer._checkout()
    buffer.start()
    buffer._checkout()
    result = None

    while True:
        if buffer.finish():
            break
        try:
            ret = buffer.read()
            ipdb.set_trace()
            if isinstance(ret, tuple):
                frame_id, frame = ret
                print('video', frame_id)
                result = frame_id
        except TimeoutError:
            print(TimeoutError)
            break
    assert result == expect
