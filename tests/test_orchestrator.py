from src.buffer_right import VideoBufferRight
from src.buffer_left import VideoBufferLeft
from src.frame_mapper import FrameMapper
from src.player_control import PlayerControl
from src.video_command import FrameUndoOrchestrator, FrameRemoveOrchestrator
from src.trash import Trash
from threading import Semaphore
from pytest import fixture
from unittest.mock import patch
import numpy as np
import cv2
import pytest
import ipdb


def lote(start, end, step=1):
    return [(frame_id, np.zeros((2, 2))) for frame_id in range(start, end, step)]


def setVideoBufferLeft(frame_id, buffer_left, buffer_right):
    buffer_left.set(frame_id)
    buffer_right.set(frame_id)


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
def orch_100(mycap, frame_count=100, buffersize=25, log=False):
    cap = mycap.return_value
    semaphore = Semaphore()

    mapping = FrameMapper(list(range(frame_count)), frame_count=frame_count)
    master = VideoBufferLeft(cap, mapping, semaphore, buffersize=buffersize, bufferlog=log, name='left')
    servant = VideoBufferRight(cap, mapping, semaphore, buffersize=buffersize, bufferlog=log, name='right')
    player_control = PlayerControl(servant, master)
    _trash = Trash(cap, semaphore, frame_count=frame_count, buffersize=5)
    yield (player_control, mapping, _trash)
    _trash.join()
    master.join()
    servant.join()


# ####### Testes do FrameRemoveOrchestrator com servant VideoBufferRight como padrão ###### #

def test_orchestrator_removendo_frame_0_com_servant_VideoBufferRight(orch_100):
    player, trash, mapping = orch_100
    player.read()
    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 1
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id


def test_orchestrator_removendo_ultimo_frame_com_servant_VideoBufferRight(orch_100):
    player, trash, mapping = orch_100
    player.servant.set(99)
    player.master.set(99)
    player.read()
    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 98
    expect_buffer = True
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id
    assert expect_buffer is isinstance(player.servant, VideoBufferLeft)


def test_orchestrator_removendo_frame_do_meio_com_servant_VideoBufferRight(orch_100):
    player, trash, mapping = orch_100
    player.servant.set(50)
    player.master.set(50)
    player.read()
    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 51
    expect_buffer = False
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id
    assert expect_buffer is isinstance(player.servant, VideoBufferLeft)


def test_orchestrator_removendo_todos_os_frames_desde_o_inicio_com_servant_VideoBufferRight(orch_100):
    player, trash, mapping = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)
    player.servant.set(50)
    player.master.set(50)
    while not player.servant.is_task_complete():
        player.read()
        remov.remove()

    expect_is_task_complete = True

    # Aqui ocorre duas trocas de buffers, a primeira ao atingir a extremidade direita,
    # a segunda ao atingir a extremidade da esquerda, portanto o buffer do final é o da direita
    # por isso o expect_buffer deve ser falso
    expect_buffer = False
    player.read()
    result_is_task_complet = player.servant.is_task_complete()
    assert expect_is_task_complete == result_is_task_complet
    assert expect_buffer is isinstance(player.servant, VideoBufferLeft)


def test_orchestrator_removendo_todos_os_frames_a_partir_da_metade_com_servant_VideoBufferRight(orch_100):
    player, trash, mapping = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)
    while not player.servant.is_task_complete():
        player.read()
        remov.remove()

    expect_is_task_complete = True
    expect_buffer = True
    player.read()
    result_is_task_complet = player.servant.is_task_complete()
    assert expect_is_task_complete == result_is_task_complet
    assert expect_buffer is isinstance(player.servant, VideoBufferLeft)


# ####### Testes do FrameRemoveOrchestrator com servant VideoBufferRight como padrão ###### #

def test_orchestrator_removendo_frame_0_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100
    player.rewind()

    player.servant.set(1)
    player.master.set(1)
    player.read()

    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 1
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id


def test_orchestrator_removendo_ultimo_frame_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100

    player.servant.set(99)
    player.master.set(99)
    player.read()
    player.rewind()

    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 98
    expect_buffer = True
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id
    assert expect_buffer is isinstance(player.servant, VideoBufferLeft)


def test_orchestrator_removendo_frame_do_meio_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100

    player.rewind()
    player.servant.set(50)  # seta o frame_id 49
    player.master.set(50)
    player.read()

    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()  # Remove o frame_id 49

    expect_frame_id = 48
    expect_buffer = False
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id
    assert expect_buffer is isinstance(player.servant, VideoBufferRight)


def test_orchestrator_removendo_todos_os_frames_a_partir_da_metade_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.rewind()
    player.servant.set(50)
    player.master.set(50)

    while not player.servant.is_task_complete():
        player.read()
        remov.remove()

    expect_is_task_complete = True

    # Aqui ocorre duas trocas de buffers, a primeira ao atingir a extremidade esquerda,
    # a segunda ao atingir a extremidade da direita, portanto o buffer do final é o da esquerda
    # por isso o expect_buffer deve ser falso
    expect_buffer = False

    player.read()
    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    assert expect_buffer is isinstance(player.servant, VideoBufferRight)


def test_orchestrator_removendo_todos_os_frames_desde_o_inicio_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.rewind()
    while not player.servant.is_task_complete():
        player.read()
        remov.remove()

    expect_is_task_complete = True
    # expect_buffer = True

    player.read()
    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    # assert expect_buffer is isinstance(player.servant, VideoBufferRight)


def test_orchestrator_removendo_todos_os_frames_desde_o_final_com_servant_VideoBufferLeft(orch_100):
    player, trash, mapping = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.servant.set(99)
    player.master.set(99)
    player.read()
    player.rewind()

    while not player.servant.is_task_complete():
        remov.remove()
        player.read()

    expect_is_task_complete = True
    # expect_buffer = True

    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    # assert expect_buffer is isinstance(player.servant, VideoBufferRight)


@pytest.mark.skip(reason='Criar os teste de exclusão primeiro')
def test_orchestrator_restaurando_o_frame_com_os_dois_buffers_vazios_exclusao_linear_para_a_direita(orch_100):
    player, trash, mapping = orch_100
    orch = FrameUndoOrchestrator(*orch_100)
    remov = FrameRemoveOrchestrator(*orch_100)

    # Removendo o frame de indice 15
    player.servant.run()
    player.read()
    [remov.remove() for _ in range(100)]

    expect_frame_id = 0
    orch.undo()
    result_frame_id = player.frame_id
    assert result_frame_id == expect_frame_id


@pytest.mark.skip(reason='Criar os teste de exclusão primeiro')
def test_orchestrator_restaurando_o_frame_com_o_indice_no_buffer_primario_do_buffer_da_direita_e_VideoBufferRight_como_servant(orch_100):
    player, trash, mapping = orch_100
    orch = FrameUndoOrchestrator(*orch_100)
    remov = FrameRemoveOrchestrator(*orch_100)

    # Removendo o frame de indice 15
    [player.read() for _ in range(16)]
    remov.remove()

    # Retornando para o frame de indice 0
    player.rewind()
    [player.read() for _ in range(16)]
    player.proceed()
    # ipdb.set_trace()

    expect_frame_id = 15
    orch.undo()
    result_frame_id = player.frame_id
    assert result_frame_id == expect_frame_id

