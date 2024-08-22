from src.my_structure import Queue
from multiprocessing import Lock
from pytest import fixture

import ipdb

def test_queua_esta_vazia():
    expect = True
    queue = Queue(maxsize=25)
    result = queue.empty()
    assert result == expect


def test_queua_nao_esta_cheia():
    expect = False
    queue = Queue(maxsize=25)
    result = queue.full()
    assert result == expect


def test_queue_qsize_fila_vazia():
    expect = 0
    queue = Queue(maxsize=25)
    result = queue.qsize()
    assert result == expect


def test_queue_put_colocando_3_dados():
    expect_empty = False
    expect_full = False
    expect_qsize = 3

    queue = Queue(maxsize=25)
    [queue._put(x) for x in [3, 2, 1]]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_put_colocando_25_dados():
    expect_empty = False
    expect_full = True
    expect_qsize = 25

    queue = Queue(maxsize=25)
    [queue._put(x) for x in range(25, 0, -1)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_put_colocando_26_dados():
    expect_empty = False
    expect_full = True
    expect_qsize = 25
    expect_values = list(range(1, 26))

    queue = Queue(maxsize=25)
    [queue._put(x) for x in range(26, 0, -1)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()
    result_values = [queue.get() for _ in range(25)]

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
    assert result_values == expect_values


def test_queue_pqueue_colocando_3_dados():
    expect_empty = False
    expect_full = False
    expect_qsize = 3

    lock = Lock()
    queue = Queue(maxsize=25, lock=lock)
    with lock:
        [queue.pqueue.put(x) for x in [1, 2, 3]]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_pqueue_colocando_25_dados():
    expect_empty = False
    expect_full = True
    expect_qsize = 25

    lock = Lock()
    queue = Queue(maxsize=25, lock=lock)
    with lock:
        [queue.pqueue.put(x) for x in range(1, 26)]
    result_empty = queue.empty()
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize


def test_queue_pqueue_colocando_25_dados_e_mais_1_manualmente():
    expect_empty = False
    expect_full = True
    expect_qsize = 25
    expect_values = list(range(1, 26))

    lock = Lock()
    queue = Queue(maxsize=25, lock=lock)
    with lock:
        [queue.pqueue.put(x) for x in range(2, 27)]
    result_empty = queue.empty()
    print(queue.queue)
    queue._put(1)
    print(queue.queue)
    result_full = queue.full()
    result_qsize = queue.qsize()
    result_values = [queue.get() for _ in range(25)]

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
    assert result_values == expect_values


def test_queue_pqueue_colocando_25_dados_e_consumindo_a_queue():
    expect_empty = True
    expect_full = False
    expect_qsize = 0

    lock = Lock()
    queue = Queue(maxsize=25, lock=lock)
    with lock:
        [queue.pqueue.put(x) for x in range(1, 26)]
    [queue.get() for _ in range(25)]
    result_empty = queue.empty()
    print(queue.queue)
    print(queue.queue)
    result_full = queue.full()
    result_qsize = queue.qsize()

    assert result_empty == expect_empty
    assert result_full == expect_full
    assert result_qsize == expect_qsize
