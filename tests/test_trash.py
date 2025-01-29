from src.trash import Trash
from src.buffer_right import VideoBufferRight
from threading import Semaphore
from pytest import fixture
from unittest.mock import patch
import numpy as np
import cv2
import pytest
import ipdb


def lote(start, end, step=1):
    return [(frame_id, np.zeros((2, 2))) for frame_id in range(start, end, step)]


@fixture
def mycap():
    with patch('cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock


class MyVideoCapture():
    def __init__(self):
        self.frames = [np.zeros((2, 2)) for x in range(500)]
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
def trash(mycap):
    cap = mycap.return_value
    semaphore = Semaphore()
    _trash = Trash(cap, semaphore, frame_count=3000, buffersize=5)
    yield _trash
    _trash.join()


def test_trash_empty(trash):
    expect = True
    result = trash.empty()
    assert expect == result


def test_trash_not_empty(trash):
    expect = False
    trash.move(0, np.zeros((2, 2)))
    result = trash.empty()
    assert expect == result


def test_adicionando_o_frame_excluido(trash):
    expect_frame_id = 0
    trash.move(0, np.zeros((2, 2)))
    result_frame_id = trash._stack[0]
    assert expect_frame_id == result_frame_id


def test_adicionando_10_frame_excluido(trash):
    expect_frames_id = [frame_id for frame_id in range(10)]
    expect_frames = 10
    [trash.move(frame_id, frame) for frame_id, frame in lote(0, 10)]
    result_frames_id = list(trash._stack)
    result_frames = len(trash._dframes)
    assert expect_frames_id == result_frames_id
    assert expect_frames == result_frames


def test_adicionando_11_frame_excluido(trash):
    expect_frames_id = [frame_id for frame_id in range(1, 11)]
    [trash.move(frame_id, frame) for frame_id, frame in lote(0, 11)]
    result_frames_id = list(trash._stack)
    trash._memento_undo()
    assert expect_frames_id == result_frames_id


def test_trash_not_full(trash):
    expect = False
    result = trash.full()
    assert expect == result


def test_trash_not_full_com_1_frame(trash):
    expect = False
    trash.move(0, np.zeros((2, 2)))
    result = trash.full()
    assert expect == result


def test_trash_full(trash):
    expect = True
    [trash.move(frame_id, frame) for frame_id, frame in lote(0, 10)]
    result = trash.full()
    assert expect == result


def test_trash_vazio_com_undo(trash):
    expect = (None, None)
    result = trash.undo()
    assert expect == result


def test_trash_com_1_frame_undo(trash):
    expect_frame_id = 0
    trash.move(0, np.zeros((2, 2)))
    result_frame_id, _ = trash.undo()
    assert expect_frame_id == result_frame_id


def test_trash_com_10_frame_undo(trash):
    expect_frames_id = list(range(9, -1, -1))
    [trash.move(frame_id, frame) for frame_id, frame in lote(0, 10)]
    result_frames_id = [trash.undo()[0] for _ in range(10)]
    assert expect_frames_id == result_frames_id


def test_trash_com_11_frame_undo(trash):
    expect_frames_id = list(range(11, 0, -1))
    [trash.move(frame_id, frame) for frame_id, frame in lote(1, 12)]
    result_frames_id = [trash.undo()[0] for _ in range(11)]
    assert expect_frames_id == result_frames_id


# @pytest.mark.skip(reason='Devo implementar depois')
def test_trash_com_20_frame_undo(trash):
    expect_frames_id = list(range(20, 0, -1))
    [trash.move(frame_id, frame) for frame_id, frame in lote(1, 21)]
    result_frames_id = [trash.undo()[0] for _ in range(20)]
    assert expect_frames_id == result_frames_id
