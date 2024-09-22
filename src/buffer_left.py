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
from src.reader import reader
from threading import Semaphore, Thread
from time import sleep
import bisect


class VideoBufferLeft:
    """
    O VideoBufferLeft começa
    """

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

        # Atributos usados para determinar os frames que serao armazenados no buffer
        self.lot = list()
        self.lot_mapping = set()
        self.set_lot(sequence_frames)

        self.thread = None
        self.__start()

    def __del__(self):
        self._buffer.send(False)

    def __len__(self):
        return len(self._buffer)

    def __getitem__(self, index: int) -> int:
        """
        Retorna os frame_id do buffer, caso o mesmo esteja vazio -1 é retornado.

        Args:
            index (int): Indice do frame na qual se deseja conhecer o frame_id
                se o mesmo não for inteiro, -1 é retornado.

        Returns:
            int
                - Em caso de sucesso um número inteiro maior que zero é retornado.
                - Em caso de falha -1 é retornado.

        """
        if self._buffer.empty() or not isinstance(index, int):
            return -1
        return self._buffer[index][0]

    def __start(self) -> None:
        """
        Inicia a thread

        Returns:
            None
        """
        if self.thread is None:
            args = (self.cap, self._buffer)
            self.thread = Thread(target=reader, args=args)
            self.thread.start()

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
        idx = temp_idx
        if idx < 0:
            self.__set_frame_end = self.lot[0]
        else:
            self.__set_frame_end = self.lot[idx]

        return frame_id

    def is_task_complete(self) -> bool:
        """
        Checa se todos os frames do lotes foram consumidos.

        Returns:
            bool
        """
        return self.__frame_id == self.lot[0]

    def is_done(self) -> bool:
        """
        Verifica se todos os frames do lote foram processados.

        Returns:
            bool
        """
        if isinstance(self._set_frame, int):
            return self.__set_frame_end == self._set_frame
        elif not self._buffer.empty():
            return self._buffer[-1][0] == self.lot[0]
        else:
            return self.is_task_complete()

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

        self.__frame_id = self.lot[0]

    def set(self, frame_id: int) -> None:
        """
        Coloco o frame a esquerda de frame_id como start_frame no próximo ciclo de leitura dos frames.
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
        self.__frame_id = None

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

    def run(self):
        if self.do_task():
            values = (self.start_frame(), self.end_frame(), self.lot_mapping)

            # O método send deve ser usado somente em 2 casos:
            #   1o. Para enviar os dados para a thread
            #   2o. Para encerrar o thread
            # Peço que usem o send somente para o 2o caso e certifique-se usando
            # _buffer.task_id_done que a task está "parada"!
            self._buffer.send(values)

            # Devemos sincronizar a thread principal com o inicio da task
            # para não corrermos o risco de acessar váriaveis que ainda não foram
            # atualizadas.
            self._buffer.synchronizing_main_thread()
            self._set_frame = None

    def join(self) -> None:
        """
        Encerra a thread

        Returns:
            None
        """

        # Caso a thread esteja fazendo uma task, devemos encerrá-la
        if not self._buffer.task_is_done():
            self._buffer.send(False)
        self._buffer.send(False)

    def put(self, frame_id: int, frame: ndarray) -> None:
        """
        Método usado para encher o buffer de maneira manual e de forma segura.

        Args:
            frame_id (int): frame_id do frame a ser colocado no buffer.
            frame (ndarray): frame a ser colocado no buffer.
        """
        if self._buffer.empty() is False:
            if self._buffer[-1][0] > frame_id and len(self._buffer._primary) > 0:
                raise Exception('inconsistencia na operação, onde frame_id é maior que o frame atual ')

        # O método put tem prioriade sobre o set, portanto devemos
        # setar ambos os atributos relacionados ao set como None.
        self._set_frame = None
        self.__set_frame_end = None

        self.__frame_id = None
        self._buffer.put((frame_id, frame))

    def get(self) -> None:
        self.run()
        self._buffer.unqueue()
        frame_id, frame = self._buffer.get()
        self.__frame_id = frame_id
        self.run()
        return frame_id, frame
