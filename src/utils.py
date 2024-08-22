from src.buffer_error import VideoOpenError
from cv2 import VideoCapture
from multiprocessing import Pipe, Lock, SimpleQueue
from pathlib3x import Path
from time import time

import cv2
import pickle
import traceback


def reader(filename: str,
           queue: SimpleQueue,
           lock: Lock,
           buffersize: int,
           bufferlog: bool,
           conn: Pipe) -> None:
    """Um invólucro que chama a função responsável por ler os frames através do modulo da Opencv.

        Args:
            filename (str): caminho até o arquivo de mídeo.
            queue (SimpleQueue): uma fila onde serão armazenadas os frames.
            lock (Lock): objeto para travar a queue na gravação do frame na mesma.
            buffersize (int): número de frames a serem armazenadas na queue.
            bufferlog (bool): ativa o log.
            conn (Pipe): canal para comunicação entre os dois processos.

    """

    def reader_task(cap: VideoCapture,
                    queue: SimpleQueue,
                    lock: Lock,
                    buffersize: int,
                    bufferlog: bool,
                    conn: Pipe) -> int:
        """Função responsável por ler os frames através do modulo da Opencv.

            Args:
                cap (VideoCapture): objeto usado para gerar os frames.
                queue (SimpleQueue): uma fila onde serão armazenadas os frames.
                lock (Lock): objeto para travar a queue na gravação do frame na mesma.
                buffersize (int): número de frames a serem armazenadas na queue.
                bufferlog (bool): ativa o log.
                conn (Pipe): canal para comunicação entre os dois processos.

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

        # Bloco onde os frames são lidos e armazenados na fila
        while True:

            if frame_id in lot:
                ret, frame = cap.read()
                if ret:
                    # with lock:
                    # Deve-se colocar o indice do frame + frame na queue
                    print('Colocando', ret, queue)
                    queue.put((frame_id))
                    print('Colocou')
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
        while True:

            # O pai deve enviar um bool para task_flag, se a mesma for True
            # a task é iniciada, se for false devemos sair do bloco while, se
            # task_flag não for bool, uma exceção deve ser levantada.
            task_flag = conn.recv()
            if task_flag is True:
                reader_task(cap, queue, lock, buffersize, bufferlog, conn)
            elif task_flag is False:
                break
            else:
                raise TypeError('A flag deve ser do tipo bool.')

    except Exception as e:
        exc_info = traceback.format_exc()
        conn.send(pickle.dumps((e, exc_info)))

    finally:
        if cap is not None:
            cap.release()
        conn.close()
