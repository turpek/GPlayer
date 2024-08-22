from src.buffer_right import VideoBufferRight
from pytest import fixture
from pathlib3x import Path
from unittest.mock import MagicMock, patch


import cv2
import numpy as np
import ipdb
from time import sleep

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


@fixture
def mycap():
    with patch('cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock


@fixture
def seq():
    sequence = [(frame_id, np.zeros((2, 2))) for frame_id in range(150)]
    return sequence


def test_buffer_VideoBufferRight_first_frame(mycap):
    expect = 0
    lote = list(range(20))
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.first_frame()
    assert result == expect


def test_buffer_VideoBufferRight_last_frame(mycap):
    expect = 19
    lote = list(range(20))
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.last_frame()
    assert result == expect


def test_buffer_VideoBufferRight_start_frame_0(mycap):
    expect = 0
    lote = list(range(20))
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.start_frame()
    assert result == expect


def test_buffer_VideoBufferRight_start_frame_15(mycap):
    expect = 15
    lote = list(range(15, 20))
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.start_frame()
    assert result == expect


def test_buffer_VideoBufferRight_sequence_linear(mycap):
    lote = list(range(0, 20))
    expect = {key for key in lote}
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.lot_mapping
    assert result == expect


def test_buffer_VideoBufferRight_metodo_end_frame(mycap):
    lote = list(range(0, 20))
    expect = 4
    buffer = VideoBufferRight('path', lote, buffersize=5)
    result = buffer.end_frame()
    assert result == expect


def test_buffer_VideoBufferRight_metodo_set_frame(mycap):
    lote = list(range(0, 150))
    expect_start_frame = 25
    expect_end_frame = 49
    buffer = VideoBufferRight('path', lote, buffersize=25)
    buffer.set(25)
    result_start_frame = buffer.start_frame()
    result_end_frame = buffer.end_frame()
    assert result_start_frame == expect_start_frame
    assert result_end_frame == expect_end_frame


def test_buffer_VideoBufferRight_metodo_set_frame_com_lote_nao_linear(mycap):
    lote = list(range(0, 200, 7))
    expect_start_frame = 28
    buffer = VideoBufferRight('path', lote, buffersize=25)
    buffer.set(25)
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


def test_buffer_VideoBufferRight_metodo_set_frame_com_lote_nao_linear_ultimo_frame(mycap):
    lote = list(range(0, 200, 7))
    expect_start_frame = 196
    buffer = VideoBufferRight('path', lote, buffersize=25)
    buffer.set(196)
    result_start_frame = buffer.start_frame()
    assert result_start_frame == expect_start_frame


def test_buffer_VideoBufferRight_enchendo_o_buffer_manualmente(mycap, seq):
    lote = list(range(0, 100))
    expect_start_frame = 9
    expect_end_frame = expect_start_frame + 24
    buffer = VideoBufferRight('path', lote, buffersize=25)
    [buffer.put(*seq.pop(0)) for _ in range(10)]
    result_start_frame = buffer.start_frame()
    result_end_frame = buffer.end_frame()
    assert result_start_frame == expect_start_frame
    assert result_end_frame == expect_end_frame
