from src.buffer import Buffer
from src.reader import reader
from tests.my_mocks import MyVideoCapture
from pytest import fixture
from unittest.mock import patch
from threading import Event, Thread
from time import sleep
import ipdb


def encher_buffer(buffer: Buffer, data):
    buffer.send(data)
    buffer.event.set()
    while True:
        sleep(0.001)
        if buffer.task_is_done():
            break


@fixture
def mycap():
    with patch('cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock


@fixture
def mybuffer():
    buffer = Buffer(maxsize=10)
    return buffer


@fixture
def buffer(mycap, mybuffer):
    event = Event()
    cap = mycap.return_value
    buffer = mybuffer
    buffer.event = event
    th = Thread(target=reader, args=(cap, buffer, event), name='reader')
    th.start()
    data = (10, 20, set(range(101)))
    encher_buffer(buffer, data)
    return buffer


def test_enchendo_o_buffer_segundario(buffer):
    expect = True
    sleep(0.02)
    result = buffer.secondary_is_full()
    buffer.send(True)
    assert result == expect


def test_fazendo_o_swap(buffer):
    expect_full = True
    expect_empty = True
    sleep(0.02)
    result_full = buffer.secondary_is_full()
    buffer.swap()
    result_empty = buffer.secondary_is_empty()

    buffer.send(True)
    assert result_full == expect_full
    assert result_empty == expect_empty


def test_enchendo_o_buffer_primario_e_secundario(buffer):
    expect = True
    buffer.swap()
    data = (10, 20, set(range(101)))
    encher_buffer(buffer, data)
    result = buffer.full()
    buffer.send(True)
    assert result == expect
