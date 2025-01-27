from src.buffer_right import VideoBufferRight
from src.buffer_left import VideoBufferLeft
from src.custom_exceptions import VideoBufferError
from src.frame_mapper import FrameMapper
from src.player_control import PlayerControl
from src.video_command import FrameUndoOrchestrator, FrameRemoveOrchestrator, RewindCommand, ProceesCommand
from src.trash import Trash
from threading import Semaphore
from pytest import fixture
from unittest.mock import patch
import numpy as np
import cv2
import pytest


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
def player(mycap, request):
    lote, buffersize = request.param
    cap = mycap.return_value
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    mapping = FrameMapper(lote, frame_count)
    semaphore = Semaphore()
    log = False
    vbuffer_right = VideoBufferRight(cap, mapping, semaphore, bufferlog=log, buffersize=buffersize)
    vbuffer_left = VideoBufferLeft(cap, mapping, semaphore, bufferlog=log, buffersize=buffersize)
    player_control = PlayerControl(vbuffer_right, vbuffer_left)
    yield player_control

    vbuffer_left.join()
    vbuffer_right.join()


@fixture
def orch(mycap, request):
    lote, buffersize, frame_count, log = request.param
    cap = mycap.return_value
    semaphore = Semaphore()

    mapping = FrameMapper(lote, frame_count=frame_count)
    master = VideoBufferLeft(cap, mapping, semaphore, buffersize=buffersize, bufferlog=log, name='left')
    servant = VideoBufferRight(cap, mapping, semaphore, buffersize=buffersize, bufferlog=log, name='right')
    player_control = PlayerControl(servant, master)
    _trash = Trash(cap, semaphore, frame_count=frame_count, buffersize=5)
    yield (player_control, mapping, _trash)
    _trash.join()
    master.join()
    servant.join()


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


@fixture
def orch_200(mycap, frame_count=200, buffersize=25, log=False):
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


# ######### Teste do RewindCommand Sem frames ###################################

@pytest.mark.parametrize('player', [([], 25)], indirect=True)
def test_RewindCommand_sem_frames(player):
    RewindCommand(player)

    expect = True
    player.rewind()
    result = isinstance(player.servant, VideoBufferLeft)
    assert expect == result


@pytest.mark.parametrize('player', [([], 25)], indirect=True)
def test_RewindCommand_sem_frames_com_read(player):
    rewind = RewindCommand(player)

    expect = False
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([], 25)], indirect=True)
def test_RewindCommand_sem_frames_com_a_seguinte_sequencia_rewind_proceed_rewind(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)

    expect = False
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    assert expect == result


# ######### Teste do RewindCommand com 1 frame #####################################

@pytest.mark.parametrize('player', [([0], 25)], indirect=True)
def test_RewindCommand_com_1_frame(player):
    RewindCommand(player)

    expect = True
    player.rewind()
    result = isinstance(player.servant, VideoBufferLeft)
    assert expect == result


@pytest.mark.parametrize('player', [([0], 25)], indirect=True)
def test_RewindCommand_com_1_frame_com_read(player):
    rewind = RewindCommand(player)
    expect = False
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0], 25)], indirect=True)
def test_RewindCommand_com_1_frame_com_a_seguinte_sequencia_rewind_proceed_rewind(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)

    expect = False
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    assert expect == result


# ######### Teste do RewindCommand com 2 frame #####################################

@pytest.mark.parametrize('player', [([0, 1], 25)], indirect=True)
def test_RewindCommand_com_2_frames(player):
    RewindCommand(player)

    expect = True
    player.rewind()
    result = isinstance(player.servant, VideoBufferLeft)
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1], 25)], indirect=True)
def test_RewindCommand_com_2_frames_com_read(player):
    rewind = RewindCommand(player)
    expect = False
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1], 25)], indirect=True)
def test_RewindCommand_com_2_frames_com_a_seguinte_sequencia_rewind_proceed_rewind(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)

    expect = False
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1], 25)], indirect=True)
def test_RewindCommand_com_2_frames_com_set_antes_do_executor(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)
    player.servant.set(1)
    player.master.set(1)

    expect = True
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1], 25)], indirect=True)
def test_RewindCommand_com_2_frames_com_set_antes_do_executor_com_read(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)
    player.servant.set(1)
    player.master.set(1)

    expect = False
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    result, _ = player.read()
    assert expect == result


# ######### Teste do RewindCommand com 3 frames #####################################

@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames(player):
    RewindCommand(player)

    expect = True
    player.rewind()
    result = isinstance(player.servant, VideoBufferLeft)
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames_com_read(player):
    rewind = RewindCommand(player)
    expect = False
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames_com_a_seguinte_sequencia_rewind_proceed_rewind(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)

    expect = True
    rewind.executor()
    procees.executor()
    rewind.executor()
    result = isinstance(player.servant, VideoBufferLeft)
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames_com_set_antes_do_executor(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)
    player.servant.set(2)
    player.master.set(2)

    expect = True
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames_com_set_antes_do_executor_com_2_read(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)
    player.servant.set(2)
    player.master.set(2)

    expect = True
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    result, _ = player.read()
    assert expect == result


@pytest.mark.parametrize('player', [([0, 1, 2], 25)], indirect=True)
def test_RewindCommand_com_3_frames_com_set_antes_do_executor_com_3_read(player):
    rewind = RewindCommand(player)
    procees = ProceesCommand(player)
    player.servant.set(2)
    player.master.set(2)

    expect = False
    rewind.executor()
    procees.executor()
    rewind.executor()
    result, _ = player.read()
    result, _ = player.read()
    result, _ = player.read()
    assert expect == result


# ####### Testes do FrameRemoveOrchestrator com servant VideoBufferRight como padrão ###### #

def test_orchestrator_removendo_frame_0_com_servant_VideoBufferRight(orch_100):
    player, mapping, trash = orch_100
    player.read()
    remov = FrameRemoveOrchestrator(*orch_100)
    remov.remove()

    expect_frame_id = 1
    player.read()
    result_frame_id = player.frame_id
    assert expect_frame_id == result_frame_id


def test_orchestrator_removendo_ultimo_frame_com_servant_VideoBufferRight(orch_100):
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100

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
    player, mapping, trash = orch_100

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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
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


def test_orchestrator_removendo_o_primeiro_frame_com_servant_buffer_leftt_e_depois_rewind_e_read_novamente(orch_100):
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.servant.set(1)
    player.rewind()

    player.read()
    remov.remove()
    player.rewind()
    player.read()

    expect_is_task_complete = True
    # expect_buffer = True

    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    # assert expect_buffer is isinstance(player.servant, VideoBufferRight)


@pytest.mark.skip(reason='Criar os teste de exclusão primeiro')
def test_orchestrator_restaurando_o_frame_com_os_dois_buffers_vazios_exclusao_linear_para_a_direita(orch_100):
    player, mapping, trash = orch_100
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
    player, mapping, trash = orch_100
    orch = FrameUndoOrchestrator(*orch_100)
    remov = FrameRemoveOrchestrator(*orch_100)

    # Removendo o frame de indice 15
    [player.read() for _ in range(16)]
    remov.remove()

    # Retornando para o frame de indice 0
    player.rewind()
    [player.read() for _ in range(16)]
    player.proceed()

    expect_frame_id = 15
    orch.undo()
    result_frame_id = player.frame_id
    assert result_frame_id == expect_frame_id


def test_orchestrator_removendo_o_ultimos_frame_e_depois_proceed_e_read_novamente(orch_100):
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.servant.set(99)
    player.master.set(99)

    player.read()
    remov.remove()
    player.proceed()
    player.read()

    expect_is_task_complete = True
    # expect_buffer = True

    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    # assert expect_buffer is isinstance(player.servant, VideoBufferRight)


def test_orchestrator_removendo_o_ultimo_frame_com_servant_buffer_left(orch_100):
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)

    player.servant.set(99)
    player.master.set(99)

    player.read()
    player.rewind()
    remov.remove()
    player.proceed()
    player.read()

    expect_is_task_complete = True
    # expect_buffer = True

    result_is_task_complet = player.servant.is_task_complete()

    assert expect_is_task_complete == result_is_task_complet
    # assert expect_buffer is isinstance(player.servant, VideoBufferRight)


def test_player_control_simulando_o_bug_ao_remover_o_1o_frame(orch_100):

    """
    ### Descrição do Problema

        <!-- Explique claramente o que está acontecendo. -->
        Logo que abrimos ativamos o modo `pause_delay` , logo em seguida mudamos para o modo `rewind`,
        removemos o 1o. f rame e apertamos `rewind` 2x seguidas, com isso o erro VideoBufferError:
        Inconsistency in operation: 'frame_id' '25' is greater than the current frame é levantado.

    ### Passos para Reproduzir (1)
        1. Enquanto a janela do opencv carrega, apertamos a tecla de barra de espaço.
        2. Apertamos a tecla "a" para entrar no modo `rewind`.
        3. Apertamos a tacla "x" para remover o 1o. frame
        4. Apertamos a tecla "a" 2x.

    ### Passos para Reproduzir (2)

        1. Enquanto a janela do opencv abre, apetamos a tecla de barra de espaço, para ativar o pause por delay
        2. Apertamos o botão 'a' 2x para o modo `rewind`
        3. Apertamos o botão 'd' para ativar o modo `proceed`
        4. Apertamos o botão 'a' 2x novamente para o modo `rewind`

    Para a simulação o passo 1. não é necessario, já que podemos controlar frame por frame, já o 2x rewind é
    simulado por 1x rewind seguido de 2x read
    """
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)
    expect = None

    player.servant.run()
    player.servant._buffer.wait_task()

    player.read()
    player.read()

    player.rewind()
    player.read()

    remov.remove()
    player.read()

    player.rewind()
    player.read()
    player.read()

    result = player.frame_id
    assert expect == result


def test_player_control_simulando_o_bug_ao_remover_o_1o_frame_versao_2(orch_100):

    """
    ### Descrição do Problema

        <!-- Explique claramente o que está acontecendo. -->
        Ao dar o pause_dalay e excluir o 1o frame o seguinte erro é levantado
        "VideoBufferError: Inconsistency in operation: 'frame_id' '1' is less than the current frame."

    ### Passos para Reproduzir

        1. Enquanto a janela do opencv abre, aperto o botão para o `pause_delay` com a tecla barra de espaço
        2. Logo em seguida aperto o 'd' 2x para mudar o modo para `rewind`
        3. Aperto o 'a' 1x para mudar o modo para `proceed`
        4. Aperto a tecla `x` para remover o 1o. frame
        5. Aperto a tecla 'd' 1x para o modo `rewind`
        6. Por último aperto 2x 'a' para o modo `proceed`

    Para a simulação o passo 1. não é necessario, já que podemos controlar frame por frame, já o 2x rewind é
    simulado por 1x rewind seguido de 2x read
    """
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)
    expect = 2

    player.servant.run()
    player.servant._buffer.wait_task()

    player.rewind()
    player.read()
    player.read()

    player.proceed()
    player.read()

    remov.remove()
    player.read()

    player.rewind()
    player.read()

    player.proceed()
    player.read()
    player.read()

    result = player.frame_id
    assert expect == result


def test_orchestrator_undo_recuperando_o_frame_do_50_com_servant_VideoBufferRight_no_frame_60(orch_100):
    player, mapping, trash = orch_100
    remov = FrameRemoveOrchestrator(*orch_100)
    undo = FrameUndoOrchestrator(*orch_100)
    expect = 50

    player.servant.set(50)
    player.master.set(50)
    player.servant.run()
    player.read()
    remov.remove()
    [player.read() for _ in range(10)]
    undo.undo()
    player.read()
    result = player.frame_id
    assert expect == result
