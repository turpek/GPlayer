from src.custom_exceptions import SimpleStackError
from src.utils import SimpleStack
from pytest import raises


def test_SimpleStack_top_sem_push():
    expect = None
    stack = SimpleStack(int)
    result = stack.top()
    assert expect == result


def test_SimpleStack_top_com_1x_push():
    expect = 1
    stack = SimpleStack(int)
    stack.push(1)
    result = stack.top()
    assert expect == result


def test_SimpleStack_top_com_2x_push():
    expect = 2
    stack = SimpleStack(int)
    stack.push(1)
    stack.push(2)
    result = stack.top()
    assert expect == result


def test_SimpleStack_pop_sem_push():
    expect = "Pop failed: Stack is empty."
    stack = SimpleStack(int)
    with raises(SimpleStackError) as excinfo:
        stack.pop()
    result = f'{excinfo.value}'
    assert expect == result


def test_SimpleStack_pop_1x_push():
    expect = 1
    stack = SimpleStack(int)
    stack.push(1)
    result = stack.pop()
    assert expect == result


def test_SimpleStack_pop_2x_push():
    expect = 2
    stack = SimpleStack(int)
    stack.push(1)
    stack.push(2)
    result = stack.pop()
    assert expect == result


def test_SimpleStack_empty_fila_vazia():
    stack = SimpleStack(int)
    assert stack.empty()


def test_SimpleStack_empty_fila_nao_vazia():
    stack = SimpleStack(int)
    stack.push(1)
    assert not stack.empty()


def test_SimpleStack_empty_fila_vazia_apos_push_e_pop():
    stack = SimpleStack(int)
    stack.push(1)
    stack.pop()
    assert stack.empty()


def test_SimplesStack_push_elemento_de_mesmo_tipo():
    stack = SimpleStack(int)
    stack.push(1)


def test_SimplesStack_push_elemento_de_tipo_diferente():
    expect = 'Expected type "int", but received "str".'
    with raises(TypeError) as excinfo:
        stack = SimpleStack(int)
        stack.push('1')
    result = str(excinfo.value)
    assert expect == result
