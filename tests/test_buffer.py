from pytest import fixture
from src.buffer import FakeBuffer as Buffer
from threading import Semaphore
import numpy as np
import pytest


@fixture
def buffer():
    semaphore = Semaphore()
    bf = Buffer(semaphore, maxsize=25)
    yield bf

def lote(start, end, step):
    return [(frame_id, np.ones((2,2))) for frame_id in range(start, end, step)]


def test_colocando_1_frame_no_buffer_secondary(buffer):
    expect = 1
    [buffer.sput(frame) for frame in lote(0, 1, 1)]
    result = buffer._secondary.qsize()
    assert expect == result


def test_enchendo_o_buffer_secondary(buffer):
    expect = True 
    [buffer.sput(frame) for frame in lote(0, 25, 1)]
    result = buffer._secondary.full()
    assert expect == result


def test_setando_o_buffer(buffer):
    expect = False
    buffer.set()
    result = buffer.task_is_done()
    assert expect == result


def test_clear_do_buffer(buffer):
    expect = True
    buffer.set()
    buffer.clear()
    result = buffer.task_is_done()
    assert expect == result
