from src.buffer import Buffer
import pytest


def test_buffer_esta_vazio():
    expect = True
    buffer = Buffer(12)
    result = buffer.empty()
    assert result == expect


def test_buffer_segundario_esta_vazio():
    expect = True
    buffer = Buffer(12)
    result = buffer.secondary_is_empty()
    assert result == expect


def test_buffer_segundario_nao_esta_vazio():
    expect = False
    buffer = Buffer(12)
    buffer.put(5)
    result = buffer.secondary_is_empty()
    assert result == expect


def test_buffer_segundario_nao_esta_cheio():
    expect = False
    buffer = Buffer(12)
    result = buffer.secondary_is_full()
    assert result == expect


def test_buffer_segundario_nao_esta_cheio_colocando_1_valor_no_mesmo():
    expect = False
    buffer = Buffer(12)
    buffer.put(5)
    result = buffer.secondary_is_full()
    assert result == expect


def test_buffer_segundario_esta_cheio():
    expect = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(12)]
    result = buffer.secondary_is_full()
    assert result == expect


def test_buffer_fazendo_o_swap_entre_os_buffers_internos():
    expect = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(12)]
    result = buffer.swap()
    assert result == expect


def test_buffer_enchendo_o_buffer():
    expect = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(12)]
    buffer.swap()
    [buffer.put(x) for x in range(12)]
    result = buffer.full()
    assert result == expect


def test_buffer_consumindo_o_buffer_primario_cheio():
    expect = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(12)]
    buffer.swap()
    [buffer.put(x) for x in range(12)]
    [buffer.get() for x in range(12)]
    buffer.swap()
    result = buffer.secondary_is_empty()
    assert result == expect


def test_buffer_consumindo_o_buffer():
    expect = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(12)]
    buffer.swap()
    [buffer.put(x) for x in range(12)]
    [buffer.get() for x in range(12)]
    buffer.swap()
    [buffer.get() for x in range(12)]
    result = buffer.empty()
    assert result == expect


def test_buffer_swap_com_o_buffer_secundario_nao_cheio():
    expect = True
    expect_empty = True
    buffer = Buffer(12)
    [buffer.put(x) for x in range(7)]
    result = buffer.swap()
    result_empty = buffer.secondary_is_empty()
    assert result == expect
    assert result_empty == expect_empty
