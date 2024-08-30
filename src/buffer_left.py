"""Este módulo fornece a classe VideoBufferLeft.

A classe VideoBufferLeft é responsável por armazenar os frames lidos atráves do
módulo da opencv, a mesma tem a seguinte estrutura:

    class VideoBufferRight(Queue):
        +cap: string que armazena o caminho até o arquivo de mídeo a ser lido.
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
from time import sleep
import bisect
import ipdb


lock = Lock()
event = Event()


class VideoBufferLeft(MyQueue):
    """Classe que implementa o buffer dos frames a serem lidos"""

    def __init__(self,
                 cap: VideoCapture,
                 sequence_frames: list[int], *,
                 buffersize=25,
                 bufferlog=False,
                 name='buffer'):

        super().__init__(maxsize=buffersize)

        # Criando as queues  para comunicação entre as threads
        parent_conn, child_conn = Channel()
        self.parent_conn = parent_conn
        self.child_conn = child_conn
        self.check = Checkout(parent_conn, event, lock)

        # Definições das variaveis que lidam com o Thread
        self.cap = cap
        self.name = name
        self.buffersize = buffersize
        self.bufferlog = bufferlog

        # Definições das variaveis responsavel pela criação do buffer
        self._start_frame = None
        self.frame_id = None
        self.__store_frame_id = None
        self._set_frame = None

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None
        self.no_block = True

    def __del__(self):
        if self.thread is not None:
            while event.is_set():
                sleep(0.1)
                event.clear()
            self.parent_conn.send(False)
        self.parent_conn.close()

    def _checkout(self):
        if self._set_frame is not None:
            self._start_frame = self._set_frame
            self._set_frame = None

    def set_lot(self, lot: list[int]) -> None:
        """
        Cria o mapping dos frames a serem lidos

        Args:
            lot (list): Lista que contem os frames_id a serem lidos
        """
        self.lot = array('l', sorted(lot))
        self.lot_mapping = set(lot)

    def first_frame(self) -> int:
        """
        Devolve o primeiro frame do lote.

        Returns:
            int: frame_id do primeiro frame do lote.
        """
        return self.lot[0]

    def last_frame(self) -> int:
        """
        Devolve o último frame do lote.

        Returns:
            int: frame_id do último frame do lote.
        """
        return self.lot[-1]

    def start_frame(self) -> int | bool:
        """
        Define o primeiro frame a ser lido em cada novo ciclo do buffer.

        Returns:
            int: retorna o frame_id.
        """
        if self._start_frame is None:
            self._start_frame = self.lot[0]
        return self._start_frame

    def set(self, frame_id: int) -> None:
        """
        Coloco o frame_id como start_frame no próximo ciclo de leitura dos frames.
        O ínicio de um novo ciclo ocorre quando o buffer esta vazio! se o frame_id não
        estiver no lote o valor setado será o valor a esquerda mais próximo do mesmo.

        Args:
            frame_id (int): id do frame a ser lido no próximo ciclo, ou seja, qu
        """
        if not isinstance(frame_id, int):
            raise TypeError('frame_id must be an integer')
        elif frame_id < 0:
            raise Exception('frame_id deve ser maior que 0.')
        temp_idx = bisect.bisect_left(self.lot, frame_id) - 1
        if (idx := temp_idx - self.buffersize) > 0:
            try:
                frame_id = self.lot[idx]
            except IndexError:
                raise IndexError('frame_id does not belong to the lot range.')
        else:
            frame_id = self.lot[0]
        self._set_frame = frame_id

    def put(self, frame_id: int, frame: ndarray) -> None:
        """
        Método usado para encher o buffer de maneira manual e de forma segura.

        Args:
            frame_id (int): frame_id do frame a ser colocado no buffer.
            frame (ndarray): frame a ser colocado no buffer.
        """
        if self._set_frame is not None:
            raise Exception('operação bloqueada até que um novo ciclo ocorra')
        elif isinstance(self.frame_id, int):
            if self.frame_id < frame_id and self.qsize() > 0:
                raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')

        self._put((frame_id, frame))
        self._start_frame = False
