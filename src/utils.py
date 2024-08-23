from src.buffer_error import VideoOpenError
from cv2 import VideoCapture
from multiprocessing import Pipe, shared_memory
from pathlib3x import Path
from time import time

import cv2
import numpy as np
import pickle
import traceback


READINESS = 0
READING = 1
CLEANING = 2
EXCEPTION = 3


def reader(filename: str,
           conn: Pipe,
           buffersize: int,
           bufferlog: bool) -> None:
    """Um invólucro que chama a função responsável por ler os frames através do modulo da Opencv.

        Args:
            filename (str): caminho até o arquivo de mídeo.
            conn (Pipe): canal para comunicação entre os dois processos.
            buffersize (int): número de frames a serem armazenadas na queue.
            bufferlog (bool): ativa o log.

    """

    def reader_task(cap: VideoCapture,
                    conn: Pipe,
                    buffersize: int,
                    bufferlog: bool) -> int:
        """Função responsável por ler os frames através do modulo da Opencv.

            Args:
                cap (VideoCapture): objeto usado para gerar os frames.
                conn (Pipe): canal para comunicação entre os dois processos.
                buffersize (int): número de frames a serem armazenadas na queue.
                bufferlog (bool): ativa o log.

            Returns:
                int: retorna o frame_id do 1o. frame a ser lido no próximo ciclo

        """

        # O pai precissa passar o frame inicial e lote de frames
        # start_frame define o frame incial, ja lot é um set contendo todos
        # os frames a serem lidos
        start_frame, lot = conn.recv()
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

        # Enviando o sinal de leitura do frames
        conn.send(READING)
        shm_list = list()

        # Bloco onde os frames são lidos e armazenados na fila
        while True:

            print(frame_id)
            if frame_id in lot:
                ret, frame = cap.read()
                if ret:
                    shm_name = f'frame_id={frame_id}'
                    shm = shared_memory.SharedMemory(name=shm_name,
                                                     create=True,
                                                     size=frame.nbytes)
                    shared_frame = np.ndarray(frame.shape, dtype=frame.dtype, buffer=shm.buf)
                    shared_frame[:] = frame[:]
                    conn.send((frame_id, shm_name, frame.shape, frame.dtype))
                    shm_list.append(shm)
                    qsize += 1
            else:
                print('grab')
                cap.grab()

            if bufferlog:
                print(qsize, qsize, frame_id)
            if qsize == buffersize:
                print('Saindo normal')
                break
            frame_id += 1

        if bufferlog:
            end = time()
            count = frame_id - start_frame
            print(f'\nLidos {count} em {end - start}s')
            print(f'{count / (end - start):.2f} FPS')

        # Enviando o sinal para a limpeza
        conn.send(CLEANING)
        clean_flag = conn.recv()
        if clean_flag is True:
            for shm in shm_list:
                print(f'filho fechou {shm.name}')
                shm.close()
                shm.unlink()
        conn.send(READINESS)

        return frame_id

    cap = None
    try:
        file = Path(filename)
        if not file.is_file():
            raise FileNotFoundError(f'Não foi possível encontrar o arquivo {file}.')

        cap = cv2.VideoCapture(str(file))
        if not cap.isOpened():
            raise VideoOpenError(f'Não foi possível abrir o arquivo {file}.')

        # Bloco "príncipal" da função, que é responsavel por ativar a leitura dos
        # frames por meio da função reader_task.
        conn.send(READINESS)
        while True:

            # O pai deve enviar um bool para task_flag, se a mesma for True
            # a task é iniciada, se for false devemos sair do bloco while, se
            # task_flag não for bool, uma exceção deve ser levantada.
            task_flag = conn.recv()
            if task_flag is True:
                reader_task(cap, conn, buffersize, bufferlog)
            elif task_flag is False:
                break
            else:
                raise TypeError('A flag deve ser do tipo bool.')

    except Exception as e:
        exc_info = traceback.format_exc()

        print(e)
        # Enviando o sinal de exceção!
        conn.send(EXCEPTION)
        conn.send(pickle.dumps((e, exc_info)))

    finally:
        if cap is not None:
            cap.release()
        print('fILHO FOI FECHADO...')
        conn.close()
