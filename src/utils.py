from src.buffer_error import VideoOpenError
from cv2 import VideoCapture
from threading import Lock
from time import time
from queue import Queue
from src.channel import Channel

import cv2
import traceback


# Sinais usados para iniciar um ciclo de leitura dos frames
BUFFER_RIGHT = 'BUFFER_RIGHT'
BUFFER_LEFT = 'BUFFER_LEFT'


def reader(cap: VideoCapture,
           queue: Queue,
           conn: Channel,
           event,
           buffersize: int,
           bufferlog: bool) -> None:
    """Um invólucro que chama a função responsável por ler os frames através do modulo da Opencv.

        Args:
            cap (str): instancia de VideoCapture.
            queue (Queue): Fila onde os frames serão armazenados.
            notify (Queue): Queue para fazer a comunicação entre as threads e a linha principal do programa.
            notify_error (Queue): Queue para fazer a comunicação de erros
            buffersize (int): número de frames a serem armazenadas na queue.
            bufferlog (bool): ativa o log.

    """

    def reader_task(cap: VideoCapture,
                    queue: Queue,
                    conn: Channel,
                    buffersize: int,
                    bufferlog: bool) -> int:
        """Função responsável por ler os frames através do modulo da Opencv.

            Args:
                cap (VideoCapture): objeto usado para gerar os frames.
                queue (Queue): Fila onde os frames serão armazenados.
                buffersize (int): número de frames a serem armazenadas na queue.
                bufferlog (bool): ativa o log.

            Returns:
                int: retorna o frame_id do 1o. frame a ser lido no próximo ciclo

        """

        # O fluxo principal do programa deve passar o frame_id "start_frame" que
        # define o  frame incial, ja lot é um set contendo todos os frames a serem lidos.
        start_frame, last_frame, lot = conn.recv()
        frame_id, qsize = start_frame, 0
        start = time()

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
                    queue.put_nowait((frame_id, frame))
                    qsize += 1
            else:
                cap.grab()

            if bufferlog:
                print(qsize, qsize, frame_id)
            if qsize == buffersize:
                break
            elif frame_id == last_frame:
                break
            elif frame_id == frame_count:
                raise IndexError('o video acabou')
            frame_id += 1

        if bufferlog:
            end = time()
            count = frame_id - start_frame
            print(f'\nLidos {count} em {end - start}s')
            print(f'{count / (end - start):.2f} FPS')

        return frame_id

    try:
        if not cap.isOpened():
            raise VideoOpenError('Não foi possível abrir o arquivo.')

        # Bloco "príncipal" da função, que é responsavel por ativar a leitura dos
        # frames por meio da função reader_task.
        while True:

            # O pai deve enviar um bool para task_flag, se a mesma for True
            # a task é iniciada, se for false devemos sair do bloco while, se
            # task_flag não for bool, uma exceção deve ser levantada.
            signal = conn.recv()
            if signal is True:
                event.wait()
                reader_task(cap, queue, conn, buffersize, bufferlog)
                event.clear()
            elif signal is False:
                break

    except Exception as e:
        exc_info = traceback.format_exc()
        conn.send((e, exc_info))

    finally:
        if cap is not None:
            cap.release()
