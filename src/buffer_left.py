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
        self._buffer = BufferLeft(semaphore, maxsize=buffersize, log=bufferlog)

        # Definições das variaveis responsavel pela criação do buffer
        self.__frame_id = None
        self._set_frame = None
        self.__set_frame_end = None
        self.__is_done = False

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None

    def __del__(self):
        ...

    def __len__(self):
        return len(self._buffer)

    def __calc_frame(self, frame_id: int) -> int:
        """
        Calcula o start_frame dado um frame_id

        Args:
            frame_id int: Identificador do frame.

        Returns:
            int
        """
        temp_idx = bisect.bisect_left(self.lot, frame_id)
        if (idx := temp_idx - self.buffersize) > 0:
            try:
                frame_id = self.lot[idx]
            except IndexError:
                raise IndexError('frame_id does not belong to the lot range.')
        else:
            frame_id = self.lot[0]

        # calculo para o metodo end_frame
        idx = temp_idx - 1
        if idx < 0:
            self.__set_frame_end = self.lot[0]
        else:
            self.__set_frame_end = self.lot[idx]

        return frame_id

    def is_done(self) -> bool | None:
        """
        Verifica se todos os frames do lote foram processados.

        Returns:
            bool | None
        """
        import ipdb
        ipdb.set_trace()
        if self.__is_done:
            return True
        elif isinstance(self._set_frame, int):
            return self.__set_frame_end == self._set_frame
        elif self._buffer.empty():
            return False
        return self._buffer[-1][0] == self.lot[0]

    def do_task(self) -> bool:
        """
        Verifica se uma task pode ser iniciada.

        Returns:
            bool
        """
        return self._buffer.do_task() and self.is_done() is False

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
        self._set_frame = self.__calc_frame(frame_id)
        self._buffer.clear_buffer()
        self.__is_done = False

    def end_frame(self) -> int:
        if isinstance(self._set_frame, int):
            return self.__set_frame_end
        elif self._buffer.empty() is False:
            idx = bisect.bisect_left(self.lot, self._buffer[-1][0]) - 1
            if idx < 0:
                return self.lot[0]
            else:
                return self.lot[idx]
        else:
            return self.lot[0]

    def start_frame(self) -> int:
        if isinstance(self._set_frame, int):
            return self._set_frame
        elif self._buffer.empty() is False:
            return self.__calc_frame(self._buffer[-1][0])
        else:
            return self.lot[0]

    def put(self, frame_id: int, frame: ndarray) -> None:
        """
        Método usado para encher o buffer de maneira manual e de forma segura.

        Args:
            frame_id (int): frame_id do frame a ser colocado no buffer.
            frame (ndarray): frame a ser colocado no buffer.
        """
        if self._buffer.empty() is False:
            if self._set_frame is not None:
                raise Exception('operação bloqueada até que um novo ciclo ocorra')
            if self._buffer[-1][0] > frame_id and len(self._buffer._primary) > 0:
                raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')

        self._buffer.put((frame_id, frame))

    def get(self) -> None:

        frame_id, frame = self._buffer.get()
        if frame_id == self.lot[0]:
            self.__is_done = True
        return True, frame
