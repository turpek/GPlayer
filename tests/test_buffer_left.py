from pytest import fixture
from src.buffer import BufferLeft
from threading import Semaphore
import numpy as np
import pytest
import ipdb


@fixture
def buffer():
    semaphore = Semaphore()
    bf = BufferLeft(semaphore, maxsize=25)
    yield bf

def lote(start, end, step):
    return [(frame_id, np.ones((2,2))) for frame_id in range(start, end, step)]


def test_buffer_left_unqueue_de_1_elemento(buffer):
    expect = False
    [buffer.sput(frame) for frame in lote(0, 1, 1)]
    buffer.unqueue()
    result = buffer.empty()
    assert result == expect


def test_buffer_left_unqueue_da_queue_full(buffer):
    expect = True
    [buffer.sput(frame) for frame in lote(0, 25, 1)]
    buffer.unqueue()
    result = buffer.full()
    assert result == expect


def test_buffer_left_put_1_elemento(buffer):
    expect = 50
    [buffer.sput(frame) for frame in lote(25, 50, 1)]
    buffer.unqueue()
    [buffer.put(frame) for frame in lote(50, 51, 1)]
    result = buffer.get()[0]
    assert result == expect


def test_buffer_left_enchendo_o_buffer_secondary_2_vezes_e_colocando_1_elemento_com_put(buffer):
    expect_block = False
    expect_sempty = True
    expect_frame_id = 75
    [buffer.sput(frame) for frame in lote(50, 75, 1)]
    buffer.unqueue()
    [buffer.sput(frame) for frame in lote(25, 50, 1)]
    [buffer.put(frame) for frame in lote(75, 76, 1)]
    result_block = buffer.no_block_task()
    result_sempty = buffer.sempty()
    result_frame_id = buffer.get()[0]
    assert result_block == expect_block
    assert result_sempty == expect_sempty
    assert result_frame_id == expect_frame_id
