from pytest import fixture
from src.my_structure import MyQueue
from threading import Lock

# import ipdb
import numpy as np


@fixture
def my_queue():
    lock = Lock()
    queue = MyQueue(lock, maxsize=25)
    return queue


def test_queua_esta_vazia(my_queue):
    expect = True
    queue = my_queue
    result = queue.empty()
    assert result == expect


def test_queua_nao_esta_cheia(my_queue):
    expect = False
    queue = my_queue
    result = queue.full()
    assert result == expect


def test_queue_qsize_fila_vazia(my_queue):
    expect = 0
    queue = my_queue
    result = queue.qsize()
    assert result == expect


def test_queue_put_colocando_3_dados(my_queue):
    expect_empty = False
    expect_full = False
    expect_qsize = 3

    queue = my_queue
    [queue._put((x, np.ones((2, 2)))) for x in [3, 2, 1]]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_put_colocando_25_dados(my_queue):
    expect_empty = False
    expect_full = True
    expect_qsize = 25

    queue = my_queue
    [queue._put((x, np.ones((2, 2)))) for x in range(25, 0, -1)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_put_colocando_26_dados(my_queue):
    expect_empty = False
    expect_full = True
    expect_qsize = 25
    expect_values = list(range(1, 26))

    queue = my_queue
    [queue._put((x, np.ones((2, 2)))) for x in range(25, 0, -1)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()
    result_values = [queue.get()[0] for _ in range(25)]

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
    assert result_values == expect_values


def test_queue_tqueue_colocando_3_dados(my_queue):
    expect_empty = False
    expect_full = False
    expect_qsize = 3

    queue = my_queue
    [queue.tqueue.put_nowait(((x, np.ones((2, 2))))) for x in [1, 2, 3]]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_tqueue_colocando_25_dados(my_queue):
    expect_empty = False
    expect_full = True
    expect_qsize = 25

    queue = my_queue
    [queue.tqueue.put_nowait(((x, np.ones((2, 2))))) for x in range(1, 26)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_tqueue_colocando_25_dados_e_mais_1_manualmente(my_queue):
    expect_empty = False
    expect_full = True
    expect_qsize = 25
    expect_values = list(range(1, 26))

    queue = my_queue
    [queue.tqueue.put_nowait(((x, np.ones((2, 2))))) for x in range(2, 27)]
    result_empty = queue.empty()
    queue._put((1, np.ones((2, 2))))
    result_full = queue.full()
    result_qsize = queue.qsize()
    result_values = [queue.get()[0] for _ in range(25)]

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
    assert result_values == expect_values


def test_queue_tqueue_colocando_25_dados_e_consumindo_a_queue(my_queue):
    expect_empty = True
    expect_full = False
    expect_qsize = 0

    queue = my_queue
    [queue.tqueue.put_nowait(((x, np.ones((2, 2))))) for x in range(1, 26)]
    [queue.get() for _ in range(25)]
    result_empty = queue.empty()
    print(queue.queue)
    print(queue.queue)
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
