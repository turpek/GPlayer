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
from multiprocessing import Pipe, Process
from numpy import ndarray
from src.buffer_error import VideoBufferError
from src.my_structure import Queue
from src.utils import reader

import bisect
from src.utils import READINESS
# import ipdb


class VideoBufferRight(Queue):
    """Classe que implementa o buffer dos frames a serem lidos"""

    def __init__(self,
                 path: str,
                 sequence_frames: list[int],
                 buffersize=25, *,
                 bufferlog=False,
                 name='buffer'):

        # Criando os pipe para comunicação entre os processos
        parent_conn, child_conn = Pipe()
        self.parent_conn = parent_conn
        self.child_conn = child_conn

        super().__init__(parent_conn, maxsize=buffersize)

        # Definições das variaveis que lidam com o Thread
        self.path = path
        self.name = name
        self.buffersize = buffersize
        self.bufferlog = bufferlog

        # Definições das variaveis responsavel pela criação do buffer
        self._start_frame = None
        self._old_frame = None
        self.__store_frame_id = None

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.process = None
        self.delay = 0.005

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

    def start_frame(self) -> int|bool:
        """Define o primeiro frame a ser lido em cada novo ciclo do buffer.

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
            self._start_frame = self.lot[0]
        return self._start_frame

    def set_lot(self, lot: list[int]) -> None:
        """Cria o mapping dos frames a serem lidos

            Args:
                lot (list): Lista que contem os frames_id a serem lidos
        """
        self.lot = array('l', sorted(lot))
        self.lot_mapping = set(lot)
        self._old_frame = self.lot[0]

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
        self._old_frame = None

    def put(self, frame_id: int, frame: ndarray) -> None:
        """Método usado para encher o buffer de maneira manual e de forma segura.

            Args:
                frame_id (int): frame_id do frame a ser colocado no buffer.
                frame (ndarray): frame a ser colocado no buffer.
        """
        if self._old_frame is None:
            raise Exception('operação bloqueada até que um novo ciclo ocorra')
        elif self._old_frame < frame_id and self.qsize() > 0:
            raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')
        self._put((frame_id, frame))
        self._start_frame = False
        self._old_frame = frame_id

    def start(self):

        if not self.empty():
            raise VideoBufferError('buffer is not empty')
        elif self.process is None:
            # Argumentos para a função reader
            args = (self.path, self.child_conn, self.buffersize, self.bufferlog)
            process = Process(target=reader, name=self.name, args=args)
            process.start()
            self.process = process
            value = self.parent_conn.recv()
            if value == READINESS:
                self.parent_conn.send(True)

        self.parent_conn.send((self.start_frame(), self.lot))

    def read(self):
        # Metodo para o comsumo do buffer, retorna None quando a pilha estiver vazia
        if not self.empty():
            frame_id, frame = self.get()
            self.__store_frame_id = frame_id
            return (frame_id, frame)
        else:
            if self.start_frame() is False:
                self.set(self.__store_frame_id + 1)
            self.start()
        return None


