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
from src.buffer import BufferLeft
from threading import Semaphore
import bisect


class VideoBufferLeft:

    def __init__(self,
                 cap: VideoCapture,
                 sequence_frames: list[int],
                 semaphore: Semaphore, *,
                 buffersize=25,
                 bufferlog=False,
                 name='buffer'):

        # Definições das variaveis que lidam com o Thread
        self.cap = cap
        self.name = name
        self.buffersize = buffersize
        self.buffer = BufferLeft(semaphore, maxsize=buffersize, log=bufferlog)

        # Definições das variaveis responsavel pela criação do buffer
        self.__frame_id = None
        self._set_frame = None

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None

    def __del__(self):
        ...

    def __len__(self):
        return len(self.buffer)

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
        estiver no lote o valor setado será o valor a esquerda mais próximo do mesmo.

        Args:
            frame_id (int): id do frame a ser lido no próximo ciclo, ou seja, qu
        """
        if not isinstance(frame_id, int):
            raise TypeError('frame_id must be an integer')
        elif frame_id < 0:
            raise Exception('frame_id deve ser maior que 0.')
        temp_idx = bisect.bisect_left(self.lot, frame_id)
        if (idx := temp_idx - self.buffersize) > 0:
            try:
                frame_id = self.lot[idx]
            except IndexError:
                raise IndexError('frame_id does not belong to the lot range.')
        else:
            frame_id = self.lot[0]
        self._set_frame = frame_id
        self.buffer.clear_buffer()

    def start_frame(self):
        if isinstance(self._set_frame, int):
            return self._set_frame
        elif self.buffer.empty() is False:
            return self.buffer[-1][0]
        else:
            return self.lot[0]

    def put(self, frame_id: int, frame: ndarray) -> None:
        """
        Método usado para encher o buffer de maneira manual e de forma segura.

        Args:
            frame_id (int): frame_id do frame a ser colocado no buffer.
            frame (ndarray): frame a ser colocado no buffer.
        """
        if self.buffer.empty() is False:
            if self._set_frame is not None:
                raise Exception('operação bloqueada até que um novo ciclo ocorra')
            if self.buffer[-1][0] > frame_id and len(self.buffer._primary) > 0:
                raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')

        self.buffer.put((frame_id, frame))

    def get(self) -> None:

        frame_id, frame = self.buffer.get()
        self.__frame_id = frame_id
        return True, frame
