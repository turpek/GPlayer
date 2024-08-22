"""Este módulo fornece a classe VideoBufferRight.

A classe VideoBufferRight é responsável por armazenar os frames lidos atráves do
módulo da opencv, a mesma tem a seguinte estrutura:

    class VideoBufferRight(Queue):
        +path: string que armazena o caminho até o arquivo de mídeo a ser lido.
        +name: string que da o nome do buffer.
        +buffersize: inteiro que determina o tamanho do buffer.
        +sequence_frames_ord: lista que fornece os frames a serem lidos.
        +sequence_frames: dicionário que mapeia os frames a serem lidos.
        +process: Processo que roda em paralelo com o programa principal, na qual os frames serão lidos
        -_end_frame: inteiro que armazena o id do último frame a ser lido
        -_start_frame: inteiro que armazenao o id do primeiro frame a ser lido
        +parent_conn: pipe para comunicação com o processo descrito acima
        +child_conn: pipe passado para o processo descrito acima

        +start_frame() int: metodo que retorna o id do primeiro frame a ser lido
        +end_frame() int: metodo que retorna o id do último frame a ser lido

"""


from array import array
from cv2 import VideoCapture
from multiprocessing import Pipe, Process
from numpy import ndarray
from pathlib3x import Path
from src.buffer_error import VideoBufferError
from src.my_structure import Queue
from time import sleep, time

import bisect
import cv2
import ipdb


class VideoBufferRight(Queue):
    """Classe que implementa o buffer dos frames a serem lidos"""

    def __init__(self,
                 path: str,
                 sequence_frames: list[int],
                 buffersize=25, *,
                 bufferlog=False,
                 name='buffer'):

        super().__init__(maxsize=buffersize)

        # Definições das variaveis que lidam com o Thread
        self.path = path
        self.name = name
        self.buffersize = buffersize
        self.bufferlog = bufferlog

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.process = None
        self.delay = 0.005

        # Definições das variaveis responsavel pela criação do buffer
        self._end_frame = None
        self._start_frame = None

        # Criando os pipe para comunicação entre os processos
        parent_conn, child_conn = Pipe()
        self.parent_conn = parent_conn
        self.child_conn = child_conn

    def first_frame(self) -> int:
        """Devolve o primeiro frame do lote.

            Returns:
                int: frame_id do primeiro frame do lote.
        """
        return self.lot[0]

    def last_frame(self) -> int:
        """Devolve o último frame do lote.

            Returns:
                int: frame_id do último frame do lote.
        """
        return self.lot[-1]

    def start_frame(self) -> int:
        """Primeiro frame a ser lido pelo buffer.

            Returns:
                int: retorna o frame_id do 1o. frame.
        """
        if self._start_frame is None:
            self._start_frame = self.lot[0]
        return self._start_frame

    def end_frame(self) -> None:
        """Último frame a ser lido pelo buffer.

            Returns:
                int: retorna o frame_id do No. frame, onde N =< buffersize
        """
        if self._end_frame is None:
            start_frame = self.start_frame()
            idx = start_frame + self.buffersize - 1
            if idx >= len(self.lot):
                idx = -1
            self._end_frame = self.lot[idx]

        return self._end_frame

    def set_lot(self, lot: list[int]) -> None:
        """Cria o mapping dos frames a serem lidos

            Args:
                lot (list): Lista que contem os frames_id a serem lidos
        """
        self.lot = array('l', sorted(lot))
        self.lot_mapping = set(lot)

    def set(self, frame_id: int) -> None:
        """Coloco o frame_id como start_frame no próximo ciclo de leitura dos frames.
        O ínicio de um novo ciclo ocorre quando o buffer esta vazio! se o frame_id não
        estiver no lote o valor setado será o valor a direita mais próximo do mesmo.

            Args:
                frame_id (int): id do frame a ser lido no próximo ciclo, ou seja, qu

        """
        if not isinstance(frame_id, int):
            raise TypeError('frame_id must be an integer')
        if frame_id not in self.lot_mapping:
            idx = bisect.bisect_right(self.lot, frame_id)
            try:
                frame_id = self.lot[idx]
            except IndexError:
                raise IndexError('frame_id does not belong to the lot range.')

        self._start_frame = frame_id
        self._end_frame = None

    def put(self, frame_id: int, frame: ndarray) -> None:
        """Método usado para encher o buffer de maneira manual e de forma segura.

            Args:
                frame_id (int): frame_id do frame a ser colocado no buffer.
                frame (ndarray): frame a ser colocado no buffer.
        """
        self.set(frame_id)
        self._put((frame_id, frame))

    """
    def start(self):

        if not self.empty():
            raise VideoBufferError('buffer is not empty')

        def reader(cap, stack, count_frame, sequence_frames, end_frame, bufferlog, conn):
            # Função responsavel por carregar a stack

            start = time()
            count, qsize = 0, 0
            while True:
                with self.lock:
                    ret, frame = cap.read()

                if ret and sequence_frames.get(count_frame):
                    with self.lock:
                        # Deve-se colocar o indice do frame + frame na stack
                        stack.put((count_frame, frame))
                        qsize += 1

                if bufferlog:
                    print(qsize, count_frame, end_frame)
                if count_frame == end_frame:
                    break
                conn.send(count_frame)
                count_frame += 1
                count += 1

            end = time()
            if bufferlog:
                print(f'\nLidos {count} em {end - start}s')
                print(f'{count / (end - start):.2f} FPS')

        def task(path, queue, bufferlog, conn):
            cap = cv2.VideoCapture(str(path))
            while True:
                task_flag = conn.recv()
                if task_flag is True:
                    count_frame, seq_frames, end_frame = conn.recv()
                    cap.set(cv2.CAP_PROP_POS_FRAMES, count_frame)
                    reader(cap, queue, count_frame, seq_frames, end_frame, bufferlog, conn)
                elif task_flag is False:
                    break
                else:
                    raise Exception('Erro: a flag deve ser bool')

            conn.close()

        # Argumentos para a função reader
        args = (self.path, self.queue, self.bufferlog, self.child_conn)
        process = Process(target=reader, name=self.name, args=args)
        process.start()
        self.parent_conn.send(True)
        self.parent_conn.send(count_frame, self.sequence_frames, self.end_frame())
        self.process = process
    """

    def read(self):
        # Metodo para o comsumo do buffer, retorna None quando a pilha estiver vazia
        if not self.empty():
            frame_id, frame = self.get()
            if frame_id == self.end_frame:
                self.join()
            return (frame_id, frame)
        return None


