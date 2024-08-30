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



class VideoBufferRight(MyQueue):
    """Classe que implementa o buffer dos frames a serem lidos"""

    def __init__(self,
                 cap: VideoCapture,
                 sequence_frames: list[int], *,
                 buffersize=25,
                 bufferlog=False,
                 name='buffer',
                 timeout: int = 1):

        super().__init__(maxsize=buffersize)

        # Criando as queues  para comunicação entre as threads
        parent_conn, child_conn = Channel()
        self.parent_conn = parent_conn
        self.child_conn = child_conn
        self.lock = Lock()
        self.event = Event()
        self.check = Checkout(parent_conn, self.event, self.lock)

        # Definições das variaveis que lidam com o Thread
        self.cap = cap
        self.name = name
        self.buffersize = buffersize
        self.bufferlog = bufferlog
        self.timeout = 1

        # Definições das variaveis responsavel pela criação do buffer
        self._start_frame = None
        self._frame_id = None
        self.__store_frame_id = None
        self._set_frame = None
        self._finished = False
        self._is_done = False

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None
        self.no_block = True
        self.delay = 0.005

    def __del__(self):
        if self.thread is not None:
            while self.event.is_set():
                sleep(0.1)
                self.event.clear()
            self.parent_conn.send(False)
        self.parent_conn.close()

    def frame_id(self) -> int | None:
        """Metod que retorna o id do ultimo frame lido pelo metodo read.

            Returns:
                int|None: id do último frame lido, caso seja None, nenhum frame foi lido ainda
        """
        return self._frame_id

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

        Quando usado o metodo put, start_frame pode assumir o valor de False,
        passando a ter valor númerico novamente somente quando o ciclo terminar, isso
        ocorre pois, o metodo put permite colocar frames_id com valor abaixo do 1o frame
        no buffer, podendo ocorre de o frame_id não seguir a sequencia do lot, assim pulando
        frames, com isso não é muito seguro calcular o valor de start_frame, sendo mais seguro,
        consumir o buffer e acessar o último frame diretamente.

        Returns:
            int: retorna o frame_id.
        """
        if self._start_frame is None:
            self._start_frame = self.lot[0]
        return self._start_frame

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

        self._finished = False
        self._set_frame = frame_id

    def _put(self, value) -> None:
        """put(value) metodo para inserção manual dos dados na fila, tal metodo
         tem a preferencia na fila, ou seja, o dado eh colocado no inicio da fila
        """
        self._checkout()
        if self.full():
            _ = self.queue.pop()
        self.queue.insert(0, value)

    def put(self, frame_id: int, frame: ndarray) -> None:
        """Método usado para encher o buffer de maneira manual e de forma segura.

            Args:
                frame_id (int): frame_id do frame a ser colocado no buffer.
                frame (ndarray): frame a ser colocado no buffer.
        """
        if self._set_frame is not None:
            raise Exception('operação bloqueada até que um novo ciclo ocorra')
        elif isinstance(self._frame_id, int):
            if self._frame_id < frame_id and self.qsize() > 0:
                raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')

        self._put((frame_id, frame))
        self._start_frame = False

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

    def join(self):
        self.event.clear()
        self.parent_conn.send(False)

    def read(self):
        # Metodo para o comsumo do buffer, retorna None quando a pilha estiver vazia

        self.check.timeout(self)
        frame_id, frame = self.get()
        self._frame_id = frame_id
        self._start_frame = frame_id + 1
        self._checkout()
        return (frame_id, frame)

    def _checkout(self):
        self.check.is_finished(self)
        self.check.check_queue(self.queue, self.tqueue)
        self.check.channel()
        self.check.error_channel()
        self.check.is_done(self)

        if len(self.queue) == 0:
            if self.start_frame() is False and self._set_frame is None:
                self.set(self._frame_id + 1)
            if self._set_frame is not None:
                self._start_frame = self._set_frame
                self._set_frame = None
            self.check.fill_buffer(self.start_frame(), self.last_frame(), self.lot_mapping)


    def finish(self):
        return self._finished
