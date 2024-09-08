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
        -_start_frame: inteiro que armazenao o id do primeiro frame a ser lido
        +parent_conn: pipe para comunicação com o processo descrito acima
        +child_conn: pipe passado para o processo descrito acima

        +start_frame() int: metodo que retorna o id do primeiro frame a ser lido

"""


from array import array
from cv2 import VideoCapture
from numpy import ndarray
from queue import Queue
from src.buffer_error import VideoBufferError
from src.checkout import Checkout
from src.my_structure import MyQueue
from src.channel import Channel
from src.utils import reader, BUFFER_RIGHT
from threading import Event, Thread, Lock
from time import sleep, time

import bisect
import ipdb



class VideoBufferRight():
    """Classe que implementa o buffer dos frames a serem lidos"""

    def __init__(self,
                 cap: VideoCapture,
                 sequence_frames: list[int], *,
                 buffersize=25,
                 bufferlog=False,
                 name='buffer',
                 timeout: int = 1):


        self.lock = Lock()

        # Definições das variaveis que lidam com o Thread
        self.cap = cap
        self.name = name
        self.buffersize = buffersize
        self.bufferlog = bufferlog

        # Definições das variaveis responsavel pela criação do buffer
        self._frame_id = None
        self._set_frame = None

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None

    def __del__(self):
        ...

    def frame_id(self) -> int | None:
        """Metod que retorna o id do ultimo frame lido pelo metodo read.

            Returns:
                int|None: id do último frame lido, caso seja None, nenhum frame foi lido ainda
        """
        return self._frame_id


    def start_frame(self) -> int:
        ...

    def set_lot(self, lot: list[int]) -> None:
        """
        Cria o mapping dos frames a serem lidos

        Args:
            lot (list): Lista que contem os frames_id a serem lidos
        """
        self.lot = array('l', sorted(lot))
        self.lot_mapping = set(lot)

    def set(self, frame_id: int) -> None:
        """
        Coloco o frame_id como start_frame no próximo ciclo de leitura dos frames.
        O ínicio de um novo ciclo ocorre quando o buffer esta vazio! se o frame_id não
        estiver no lote o valor setado será o valor a direita mais próximo do mesmo.

        Args:
            frame_id (int): id do frame a ser lido no próximo ciclo, ou seja, qu

        """
        if not isinstance(frame_id, int):
            raise TypeError('frame_id must be an integer.')
        elif frame_id < 0:
            raise Exception('frame_id deve ser maior que 0.')
        if frame_id not in self.lot_mapping:
            idx = bisect.bisect_right(self.lot, frame_id)
            try:
                frame_id = self.lot[idx]
            except IndexError:
                raise IndexError('frame_id does not belong to the lot range.')

        self._set_frame = frame_id


    def put(self, frame_id: int, frame: ndarray) -> None:
        """Método usado para encher o buffer de maneira manual e de forma segura.

            Args:
                frame_id (int): frame_id do frame a ser colocado no buffer.
                frame (ndarray): frame a ser colocado no buffer.
        """
        ...


    def start(self):

        if not self.empty():
            raise VideoBufferError('buffer is not empty')
        elif self.thread is None:
            # Argumentos para a função reader
            args = (self.cap,
                    self.tqueue,
                    self.child_conn,
                    self.event,
                    self.buffersize,
                    self.bufferlog)
            thread = Thread(target=reader, name=self.name, args=args)
            thread.start()
            self.thread = thread
            # ipdb.set_trace()
        self._checkout()

    def read(self):
        ...
