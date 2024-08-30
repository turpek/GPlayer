from pytest import fixture
from pathlib3x import Path
from queue import Queue
from src.buffer_left import VideoBufferLeft
from time import sleep
from unittest.mock import MagicMock, patch


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
    sequence = [(frame_id, np.zeros((2, 2))) for frame_id in range(10, -1, -1)]
    return sequence


@fixture
def myvideo(mycap, request):
    lote, buffersize = request.param
    cap = mycap.return_value
    buffer = VideoBufferLeft(cap, lote, buffersize=buffersize)
    return buffer


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_first_frame(myvideo):
    expect = 0
    buffer = myvideo
    result = buffer.first_frame()
    assert result == expect


@pytest.mark.parametrize('myvideo', [(list(range(200)), 5)], indirect=True)
def test_buffer_VideoBufferLeft_last_frame(myvideo):
    expect = 199
    buffer = myvideo
    result = buffer.last_frame()
    assert result == expect


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
def test_buffer_VideoBufferRight_metodo_set_frame_com_lote_nao_linear_penultimo_frame(myvideo):
    expect_start_frame = 14
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
