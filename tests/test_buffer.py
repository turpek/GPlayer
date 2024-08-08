from src.buffer import VideoBufferLeft, VideoBufferRight
from pytest import fixture
from unittest.mock import MagicMock, patch


import cv2
import numpy as np
import ipdb
from time import sleep

FILE = 'model.mp4'


@fixture
def seq1():
    SEQ1 = {
        'filename': 'video.mkv',
        'start_frame': 100,
        'end_frame': 123,
        'lot': ['0', '1', '2', '3'],
        '0': [100, 101, 102, 103, 104],
        '1': [105, 106, 107, 108, 109, 110, 111],
        '2': [112, 113, 114, 115],
        '3': [116, 117, 118, 119, 120, 121, 122, 123],
        'undo': []  # undo deve ser do tipo [(lot[str], indice[int|None], frame[list[ndarray]])]
    }
    return SEQ1


def seq2():
    SEQ2 = {
        'filename': 'video.mkv',
        'start_frame': 100,
        'end_frame': 123,
        'lot': ['0', '1', '2', '3'],
        '0': [100, 101, 102, 103, 104],
        '1': [105, 106, 107, 108, 109, 110, 111],
        '2': [112, 113, 114, 115],
        '3': [116, 117, 118, 119, 120, 121, 122, 123],
        'undo': [
            #  1o comando: c
        ]
    }
    return SEQ2


def consumidor(buffer):
    frames_id = list()
    while not buffer.empty():
        frame_id, _ = buffer.read()
        frames_id.append(frame_id)
    return frames_id

class MyVideoCapture():
    def __init__(self):
        self.frames = [np.zeros((2, 2)) for x in range(300)]
        self.index = 0

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


@fixture
def mycap():
    with patch('cv2.VideoCapture', return_value=MyVideoCapture()) as mock:
        yield mock


"""
    Sobre o preenchimento automatico do VideoBuffer: existem pelo menos 3 casod, sendo elas:
        1o -> buffer maior que a sequencia de frames restantes
        2o -> buffer igual a sequencia de frames restantes
        3o -> buffer menor que a sequenci de frames restantes

"""

# ############ Testando os pre-processamentos do buffer antes de enche-lo ###############3


def test_buffer_mount_sequence_buffer_menor_que_index_do_frame(mycap):
    expect = 5
    seq = list(range(20))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 14)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=5)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_seuquence_comparacao_da_sequencia(mycap):
    expect = {frame: True for frame in [9, 10, 11, 12, 13]}
    seq = list(range(20))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 14)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=5)
    buffer._mount_sequence()
    result = buffer.sequence_frames
    assert result == expect


def test_buffer_mount_sequence_buffer_igual_ao_index_do_frame(mycap):
    expect = 4
    seq = list(range(5))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 4)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=4)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_seuquence_buffer_igual_ao_index_do_frame_comparacao_da_sequencia(mycap):
    expect = {frame: True for frame in [0, 1, 2, 3]}
    seq = list(range(5))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 4)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=4)
    buffer._mount_sequence()
    result = buffer.sequence_frames
    assert result == expect


def test_buffer_mount_sequence_buffer_maior_que_o_index_do_frame(mycap):
    expect = 4
    seq = list(range(5))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 4)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_sequence_buffer_com_frames_nao_continuos(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]

    expect_size = 4
    expect_seq = {frame: True for frame in seq[:expect_size]}

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer._mount_sequence()

    result_size = len(buffer.sequence_frames)
    assert result_size == expect_size

    result_seq = buffer.sequence_frames
    assert result_seq == expect_seq


def test_buffer_mount_sequence_indice_do_frame_nao_pertence_ao_lot(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect_size = 10

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 231)
    ret, _ = cap.read()
    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer._mount_sequence()

    result_size = len(buffer.sequence_frames)
    assert result_size == expect_size


def test_buffer_metodo_end_frame_lido_2_frame(mycap):
    expect = 2
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 2)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.end_frame()

    assert result == expect


def test_buffer_metodo_end_frame(mycap):
    expect = 100

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.end_frame()

    assert result == expect


def test_buffer_metodo_start_frame(mycap):
    expect = 75

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.start_frame()

    assert result == expect


def test_buffer_metodo_start_frame_com_lot_de_frames_nao_continuo(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect = 90

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    result = buffer.start_frame()

    assert result == expect

# ###### Testando os metodos de enchimento do buffer usando Threads ######################### #


def test_buffer_enchendo_o_buffer_com_lot_de_frames_continuo_checagem_pelo_tamanho(mycap):
    seq = list(range(60, 120))
    expect = 25

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.qsize()
    buffer.join()

    assert result == expect


def test_buffer_enchendo_o_buffer_com_lot_de_frames_continuo_checagem_pelo_stack(mycap):
    seq = list(range(60, 120))
    expect_id_frames = [id_frame for id_frame in range(75, 100)]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.stack
    buffer.join()

    result_id_frames = [id_frame for id_frame, _ in result]
    assert result_id_frames == expect_id_frames


def test_buffer_enchendo_o_buffer_com_lot_de_frames_nao_continuo_checagem_pelo_stack(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect_id_frames = seq[:4]
    expect_size = len(expect_id_frames)

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.stack
    buffer.join()

    result_size = buffer.qsize()
    result_id_frames = [id_frame for id_frame, _ in result]

    assert result_id_frames == expect_id_frames
    assert result_size == expect_size


def test_buffer_enchendo_o_buffer_com_lot_de_1_frame(mycap):
    seq = [0, 1, 2, 3, 4]
    expect_frames_id = [0]

    cap = mycap.return_value
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.stack
    buffer.join()

    result_frames_id = [id_frame for id_frame, _ in result]

    assert result_frames_id == expect_frames_id


def test_buffer_enchendo_o_buffer_com_lot_de_1_frame_nao_continuo(mycap):
    seq = [90, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect_frames_id = [90]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.stack
    buffer.join()

    result_frames_id = [id_frame for id_frame, _ in result]

    assert result_frames_id == expect_frames_id


def test_buffer_consumindo_5_frames_do_buffer_com_lot_continuo(mycap):
    seq = list(range(60, 120))
    expect_frames_id = [99, 98, 97, 96, 95]
    expect_size = 20

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    result = [buffer.get() for _ in range(5)]
    result_frames_id = [frame_id for frame_id, _ in result]
    result_size = buffer.qsize()

    assert result_frames_id == expect_frames_id
    assert result_size == expect_size


def test_buffer_consumindo_3_frames_do_buffer_com_lot_nao_continuo(mycap):
    seq = [90, 91, 93, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect_frames_id = [98, 95, 93]
    expect_size = 2

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    result = [buffer.get() for _ in range(3)]
    result_frames_id = [frame_id for frame_id, _ in result]
    result_size = buffer.qsize()

    assert result_frames_id == expect_frames_id
    assert result_size == expect_size


def test_buffer_consumindo_todo_o_buffer_com_lot_continuo(mycap):
    seq = list(range(60, 120))
    expect = True

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    [buffer.get() for _ in range(25)]
    result = buffer.empty()

    assert result == expect


def test_buffer_consumindo_todo_o_buffer_com_lot_nao_continuo(mycap):
    seq = [90, 91, 93, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect = True

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    [buffer.get() for _ in range(5)]
    result = buffer.empty()

    assert result == expect


def test_buffer__checando_o_frame_final_do_cap(mycap):
    seq = list(range(20))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 14)
    ret, _ = cap.read()
    expect = cap.get(cv2.CAP_PROP_POS_FRAMES)

    buffer = VideoBufferLeft(cap, seq, buffersize=5)
    buffer.start()
    buffer.join()

    result = cap.get(cv2.CAP_PROP_POS_FRAMES)

    assert result == expect


def test_buffer_indice_do_frame_nao_pertence_ao_lot_checando_o_frame_final_do_cap(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 231)
    ret, _ = cap.read()
    expect = cap.get(cv2.CAP_PROP_POS_FRAMES)

    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer.start()
    buffer.join()

    result = cap.get(cv2.CAP_PROP_POS_FRAMES)

    assert result == expect

# ################  Testando o enchimento manual do buffer ##########################


# ########### TERMINA AQUI ########################################3


def test_buffer_colocando_um_frame_manual_com_buffer_vazio(mycap):
    seq = []
    frame_id = 231
    expect = 1

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer.put((frame_id, frame))
    result = buffer.qsize()

    assert result == expect


def test_buffer_colocando_dois_frames_manual_com_buffer_vazio(mycap):
    seq = []
    frame_id1 = 231
    frame_id2 = 232
    expect = 2

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)
    _, frame1 = cap.read()
    _, frame2 = cap.read()

    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    buffer.put((frame_id1, frame1))
    buffer.put((frame_id2, frame2))
    result = buffer.qsize()

    assert result == expect


def test_buffer_enchendo_o_buffer_manualmente(mycap):
    seq = []
    frame_id1 = 131
    expect = 10

    def gerador_de_frames(cap):
        frame_id = cap.get(cv2.CAP_PROP_POS_FRAMES)
        frame = cap.read()
        return (frame_id, frame)

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)

    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    [buffer.put(gerador_de_frames(cap)) for _ in range(10)]
    result = buffer.qsize()

    assert result == expect


def test_buffer_rotacao(mycap):
    seq = []
    frame_id1 = 131
    expect_frame_id = 132

    def gerador_de_frames(cap):
        frame_id = cap.get(cv2.CAP_PROP_POS_FRAMES)
        frame = cap.read()
        return (frame_id, frame)

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)

    buffer = VideoBufferLeft(cap, seq, buffersize=10)
    [buffer.put(gerador_de_frames(cap)) for _ in range(11)]
    result_frame_id = buffer.stack[0][0]

    assert result_frame_id == expect_frame_id


# ########################### AQUI ################################

# ############ TESTES DO VideoBufferRight ###########################################33


def test_buffer_mount_sequence_do_VideoBufferRight_start_frame_0(mycap):
    expect = 0
    seq = list(range(20))
    cap = mycap.return_value
    buffer = VideoBufferRight(cap, seq, buffersize=5)
    result = buffer.start_frame()
    assert result == expect


def test_buffer_mount_sequence_do_VideoBufferRight_start_frame_15(mycap):
    expect = 15
    seq = list(range(20))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 15)
    buffer = VideoBufferRight(cap, seq, buffersize=5)
    result = buffer.start_frame()
    assert result == expect


def test_buffer_mount_sequence_do_VideoBufferRight_buffer_menor_que_o_lote_de_frames(mycap):
    expect = 5
    seq = list(range(20))  # lote de frames
    cap = mycap.return_value
    buffer = VideoBufferRight(cap, seq, buffersize=5)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_seuquence_do_VideoBufferRight_comparacao_da_sequencia(mycap):
    expect = {frame: True for frame in [0, 1, 2, 3, 4]}
    seq = list(range(20))  # lote de frames
    cap = mycap.return_value
    buffer = VideoBufferRight(cap, seq, buffersize=5)
    buffer._mount_sequence()
    result = buffer.sequence_frames
    assert result == expect


def test_buffer_mount_sequence_do_VideoBufferRight_igual_ao_index_do_frame(mycap):
    expect = 4
    seq = list(range(5))
    cap = mycap.return_value
    buffer = VideoBufferRight(cap, seq, buffersize=4)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_seuquence_do_VideoBufferRight_igual_ao_index_do_frame_comparacao_da_sequencia(mycap):
    expect = {frame: True for frame in [0, 1, 2, 3]}
    seq = list(range(5))
    cap = mycap.return_value
    buffer = VideoBufferRight(cap, seq, buffersize=4)
    buffer._mount_sequence()
    result = buffer.sequence_frames
    assert result == expect


def test_buffer_mount_sequence_VideoBufferRight_maior_que_o_index_do_frame(mycap):
    expect = 2
    seq = list(range(5))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 3)
    buffer = VideoBufferRight(cap, seq, buffersize=10)
    buffer._mount_sequence()
    result = len(buffer.sequence_frames)
    assert result == expect


def test_buffer_mount_sequence_VideoBufferRight_com_frames_nao_continuos(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]

    expect_size = 9
    expect_seq = {frame: True for frame in seq[4:expect_size + 4]}

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    buffer = VideoBufferRight(cap, seq, buffersize=10)
    buffer._mount_sequence()

    result_size = len(buffer.sequence_frames)
    assert result_size == expect_size

    result_seq = buffer.sequence_frames
    assert result_seq == expect_seq


def test_buffer_VideoBufferRight_metodo_end_frame_lido_2_frame(mycap):
    expect = 26

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 2)

    buffer = VideoBufferRight(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.end_frame()

    assert result == expect


def test_buffer_VideoBufferRight_metodo_end_frame(mycap):
    expect = 124

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.end_frame()

    assert result == expect


def test_buffer_VideoBufferRight_metodo_end_frame_com_lot_menor_que_buffer(mycap):
    expect = 18

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 15)

    buffer = VideoBufferRight(cap, list(range(19)), buffersize=25, name='buffer0')
    result = buffer.end_frame()

    assert result == expect


def test_buffer_VideoBufferRight_metodo_start_frame(mycap):
    expect = 100

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, list(range(300)), buffersize=25, name='buffer0')
    result = buffer.start_frame()

    assert result == expect


def test_buffer_VideoBufferRight_metodo_start_frame_com_lot_de_frames_nao_continuo(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect = 100

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    result = buffer.start_frame()

    assert result == expect


def test_buffer_VideoBufferRight_metodo_start_frame_com_indice_do_frame_menor_que_o_indice_minimo_do_frame(mycap):
    expect = 200

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, list(range(200, 300)), buffersize=25, name='buffer0')
    result = buffer.start_frame()

    assert result == expect

def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_frames_continuo_checagem_pelo_tamanho(mycap):
    seq = list(range(60, 120))
    expect = 20

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.qsize()
    buffer.join()

    assert result == expect


def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_frames_continuo_checagem_pela_queue(mycap):
    seq = list(range(60, 120))
    expect_id_frames = [id_frame for id_frame in range(100, 120)]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.queue
    buffer.join()

    result_id_frames = [id_frame for id_frame, _ in result]
    assert result_id_frames == expect_id_frames


def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_frames_nao_continuo_checagem_pelo_queue(mycap):
    seq = [90, 91, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect_id_frames = seq[4:]
    expect_size = len(expect_id_frames)

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.queue
    buffer.join()

    result_size = buffer.qsize()
    result_id_frames = [id_frame for id_frame, _ in result]

    assert result_id_frames == expect_id_frames
    assert result_size == expect_size


def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_1_frame(mycap):
    seq = [0, 1, 2, 3, 4]
    expect_frames_id = [4]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 3)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.queue
    buffer.join()

    result_frames_id = [id_frame for id_frame, _ in result]

    assert result_frames_id == expect_frames_id


def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_1_frame_nao_continuo(mycap):
    seq = [108]
    expect_frames_id = [108]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 105)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.queue
    buffer.join()

    result_frames_id = [id_frame for id_frame, _ in result]

    assert result_frames_id == expect_frames_id


def test_buffer_VideoBufferRight_enchendo_o_buffer_com_lot_de_2_frame_nao_continuo(mycap):
    seq = [90, 100, 101, 102, 103, 104, 105, 108]
    expect_frames_id = [105, 108]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 105)

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    result = buffer.queue
    buffer.join()

    result_frames_id = [id_frame for id_frame, _ in result]

    assert result_frames_id == expect_frames_id


def test_buffer_VideoBufferRight_consumindo_5_frames_do_buffer_com_lot_continuo(mycap):
    seq = list(range(60, 150))
    expect_frames_id = [101, 102, 103, 104, 105]
    expect_size = 20

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    result = [buffer.read() for _ in range(5)]
    result_frames_id = [frame_id for frame_id, _ in result]
    result_size = buffer.qsize()

    assert result_frames_id == expect_frames_id
    assert result_size == expect_size


def test_buffer_VideoBufferRight_consumindo_3_frames_do_buffer_com_lot_nao_continuo(mycap):
    seq = [90, 91, 93, 95, 98, 100, 101, 102, 108, 109, 110, 111]
    expect_frames_id = [101, 102, 108]
    expect_size = 3

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    result = [buffer.get() for _ in range(3)]
    result_frames_id = [frame_id for frame_id, _ in result]
    result_size = buffer.qsize()

    assert result_frames_id == expect_frames_id
    assert result_size == expect_size


def test_buffer_VideoBufferRight_consumindo_todo_o_buffer_com_lot_continuo(mycap):
    seq = list(range(60, 120))
    expect = True

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    [buffer.get() for _ in range(25)]
    result = buffer.empty()

    assert result == expect


def test_buffer_VideoBufferRight_consumindo_todo_o_buffer_com_lot_nao_continuo(mycap):
    seq = [90, 91, 93, 95, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    expect = True

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 103)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=25, name='buffer0')
    buffer.start()
    buffer.join()

    [buffer.get() for _ in range(5)]
    result = buffer.empty()

    assert result == expect


def test_buffer_VideoBufferRight__checando_o_frame_final_do_cap(mycap):
    seq = list(range(20))
    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, 14)
    ret, _ = cap.read()
    expect = cap.get(cv2.CAP_PROP_POS_FRAMES)

    buffer = VideoBufferRight(cap, seq, buffersize=5)
    buffer.start()
    buffer.join()

    result = cap.get(cv2.CAP_PROP_POS_FRAMES)

    assert result == expect


def test_buffer_VideoBufferRight_colocando_um_frame_manual_com_buffer_vazio(mycap):
    seq = [231, 232]
    frame_id = 231
    expect = 1

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=10)
    buffer.put((frame_id, frame))
    result = buffer.qsize()

    assert result == expect


def test_buffer_VideoBufferRight_colocando_dois_frames_manual_com_buffer_vazio(mycap):
    seq = [231, 232, 233, 234, 235]
    frame_id1 = 231
    frame_id2 = 232

    expect = 5
    expect_frames_id = [231, 232, 233, 234, 235]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)
    _, frame1 = cap.read()
    _, frame2 = cap.read()

    buffer = VideoBufferRight(cap, seq, buffersize=10)
    buffer.start()
    buffer.join()

    # Simulando a função de voltar para trás
    buffer.put((frame_id2, frame2))
    buffer.put((frame_id1, frame1))
    result = buffer.qsize()
    result_frames_id = consumidor(buffer)

    assert result == expect
    assert result_frames_id == expect_frames_id


def test_buffer_VideoBufferRight_enchendo_o_buffer_manualmente(mycap):
    seq = [131, 132, 133, 134, 135, 136, 137, 138, 139, 140]
    frame_id1 = 140
    expect = 10
    expect_frames_id = seq

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)
    frames = [(i, cap.read()) for i in range(139, 130, -1)]
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)

    buffer = VideoBufferRight(cap, seq, buffersize=10)
    buffer.start()
    buffer.join()
    [buffer.put(v) for v in frames]
    result = buffer.qsize()
    result_frames_id = consumidor(buffer)

    assert result == expect
    assert result_frames_id == expect_frames_id


def test_buffer_VideoBufferRight_rotacao(mycap):
    seq = [131, 132, 133, 134, 135, 136, 137, 138, 139, 140]
    frame_id1 = 131
    expect_frame_id = 130
    expect_size = 10
    expect_frames_id = [expect_frame_id] + seq[:-1]

    cap = mycap.return_value
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id1)

    buffer = VideoBufferRight(cap, seq, buffersize=expect_size)
    buffer.start()
    buffer.join()

    cap.set(cv2.CAP_PROP_POS_FRAMES, expect_frame_id)
    frame = cap.read()

    buffer.put((expect_frame_id, frame))
    result_frame_id = buffer.queue[0][0]
    result_size = buffer.qsize()
    result_frames_id = [i for i, _ in buffer.queue]

    assert result_frame_id == expect_frame_id
    assert result_size == expect_size
    assert result_frames_id == expect_frames_id
