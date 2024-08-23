from src.buffer_error import VideoOpenError
from cv2 import VideoCapture
from threading import Lock
from time import time
from queue import Queue

import cv2
import numpy as np
import pickle
import traceback


# Sinais usados para iniciar um ciclo de leitura dos frames
BUFFER_RIGHT = 'BUFFER_RIGHT'
BUFFER_LEFT = 'BUFFER_LEFT'


def reader(cap: VideoCapture,
           queue: Queue,
           notify: Queue,
           notify_error: Queue,
           lock: Lock,
           buffersize: int,
           bufferlog: bool) -> None:
    """Um invólucro que chama a função responsável por ler os frames através do modulo da Opencv.

        Args:
            cap (str): instancia de VideoCapture.
            queue (Queue): Fila onde os frames serão armazenados.
            notify (Queue): Queue para fazer a comunicação entre as threads e a linha principal do programa.
            notify_error (Queue): Queue para fazer a comunicação de erros
            buffersize (int): número de frames a serem armazenadas na queue.
            lock (Lock): Objeto dp modulo threading para ler as filas de forma segura.
            bufferlog (bool): ativa o log.

    """

    def reader_task(cap: VideoCapture,
                    queue: Queue,
                    lock: Lock,
                    buffersize: int,
                    bufferlog: bool) -> int:
        """Função responsável por ler os frames através do modulo da Opencv.

            Args:
                cap (VideoCapture): objeto usado para gerar os frames.
                queue (Queue): Fila onde os frames serão armazenados.
                lock (Lock): Objeto dp modulo threading para ler as filas de forma segura.
                buffersize (int): número de frames a serem armazenadas na queue.
                bufferlog (bool): ativa o log.

            Returns:
                int: retorna o frame_id do 1o. frame a ser lido no próximo ciclo

        """

        # O fluxo principal do programa deve passar o frame_id "start_frame" que
        # define o  frame incial, ja lot é um set contendo todos os frames a serem lidos.
        start_frame, lot = queue.get()
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

            print(frame_id)
            if frame_id in lot:
                ret, frame = cap.read()
                if ret:
                    queue.put_nowait((frame_id, frame))
                    qsize += 1
            else:
                print('grab')
                cap.grab()

            if bufferlog:
                print(qsize, qsize, frame_id)
            if qsize == buffersize:
                break
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
            with lock:
                (buffer, signal) = notify.get()
            if buffer is BUFFER_RIGHT:
                if signal is True:
                    reader_task(cap, queue, lock, buffersize, bufferlog)
                elif signal is False:
                    break
                else:
                    raise TypeError('A flag deve ser do tipo bool.')
            else:
                with lock:
                    notify.put((buffer, signal))

    except Exception as e:
        exc_info = traceback.format_exc()
        with lock:
            notify_error.put_nowait((e, exc_info))

    finally:
        if cap is not None:
            cap.release()
        print('fILHO FOI FECHADO...')
