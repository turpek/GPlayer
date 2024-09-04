from src.buffer_error import VideoOpenError
from cv2 import VideoCapture
from threading import Event
from time import time
from src.buffer import Buffer

import cv2
import traceback
# import ipdb


def buffer_block(buffer: Buffer, flag: bool) -> None:
    with buffer.lock:
        buffer._task.get()
        buffer._task.put(flag)


def reader_task(cap: VideoCapture, buffer: Buffer, data: tuple) -> None:
    """Função responsável por ler os frames através do modulo da Opencv.

        Args:
            cap (VideoCapture): objeto usado para gerar os frames.
            buffer (Buffer): objeto onde os frames serão armazenados.
            event (Event): objeto para permitir que somente 1 thread trabalhe em cima do cap por vez.
            data (tuple[int, int, set]): deve passar como parametro (start_frame, last_frame, lot)

        Returns:
            None

    """

    # O fluxo principal do programa deve passar o frame_id "start_frame" que
    # define o  frame incial, ja lot é um set contendo todos os frames a serem lidos.
    start_frame, last_frame, lot = data
    frame_id, qsize = start_frame, 0
    start = time()
    buffer_block(buffer, False)

    # Verificando se cap já esta no frame inicial e se o frame_start
    # é menor que o último frame do vídeo
    check_frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if start_frame >= frame_count:
        raise IndexError('start_frame ultrapassou o limite de frames do vídeo.')
    elif check_frame_id != frame_id:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

    # Bloco onde os frames são lidos e armazenados na fila
    while True:

        if frame_id in lot:
            ret, frame = cap.read()
            if ret:
                buffer.put((frame_id, frame))
                qsize += 1
        else:
            cap.grab()

        if buffer.bufferlog:
            print(qsize, qsize, frame_id)
        if frame_id == last_frame:
            break
        elif qsize == buffer.buffersize:
            break
        elif frame_id == frame_count:
            raise IndexError('o video acabou')
        frame_id += 1

    buffer_block(buffer, True)
    if buffer.bufferlog:
        end = time()
        count = frame_id - start_frame
        print(f'\nLidos {count} em {end - start}s')
        print(f'{count / (end - start):.2f} FPS')


def reader(cap: VideoCapture, buffer: Buffer, event: Event) -> None:
    """Um invólucro que chama a função responsável por ler os frames através do modulo da Opencv.

        Args:
            cap (str): instancia de VideoCapture.
            buffer (Buffer): objeto onde os frames serão armazenados.
            event (Event): objeto para permitir que somente 1 thread trabalhe em cima do cap por vez.
    """

    try:
        if not cap.isOpened():
            raise VideoOpenError('Não foi possível abrir o arquivo.')

        # Bloco "príncipal" da função, que é responsavel por ativar a leitura dos
        # frames por meio da função reader_task.
        while True:

            data = buffer.recv()
            if hasattr(data, '__contains__'):
                event.wait()
                reader_task(cap, buffer, data)
                event.clear()
            else:
                break

    except Exception as e:
        exc_info = traceback.format_exc()
        buffer._error.put(e, exc_info)
    finally:
        if cap is not None:
            cap.release()
