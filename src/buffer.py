from numpy import ndarray
from src.buffer_error import VideoBufferError
from threading import Thread
from queue import LifoQueue, Queue
from time import time
import cv2
import ipdb


class VideoBuffer():
    def __init__(self, cap, sequence_frames: list[int], buffersize=25, *, bufferlog=False, name='buffer'):

        super().__init__()

        # Definições das variaveis que lidam com o Thread
        self.cap = cap
        self.name = name
        self.stack = list()
        self.buffersize = buffersize
        self.bufferlog = bufferlog
        self.sequence_frames_ord = sorted(sequence_frames)
        self.sequence_frames = dict()
        self.thread = None

        # Definições das variaveis responsavel pela criação do buffer
        self._end_frame = None
        self._start_frame = None
        self.current_frame = None

        # Checando a integridade dos dados
        self._checking_integrity()

        # Montando a sequencia de frames
        self._mount_sequence()

    def _checking_integrity(self):
        if self.end_frame() is None:
            raise VideoBufferError('the current frame index is not a valid index')

    def _mount_sequence(self):

        end_frame = self.end_frame()
        self.current_frame = end_frame

        if len(self.sequence_frames_ord) == 0:
            ...
        elif end_frame not in self.sequence_frames_ord:
            self.sequence_frames = {pos: True for pos in self.sequence_frames_ord}
            self._end_frame = self.sequence_frames_ord[-1]
        elif end_frame > 0:
            index = self.sequence_frames_ord.index(end_frame)
            seqs = self.sequence_frames_ord[:index]

            if index >= self.buffersize:
                frame0 = index - self.buffersize
            else:
                frame0 = 0
            self.sequence_frames = {pos: True for pos in seqs[frame0: index]}
        elif end_frame == 0:
            index = self.sequence_frames_ord.index(end_frame)
            self.sequence_frames = {self.sequence_frames_ord[index]: True}

    def reflesh(self, sequence_frames):
        # Metodo que atualiza o buffer

        # Variaveis a serem atualizadas
        self.stack = list()
        self.sequence_frames_ord = sorted(sequence_frames)
        self.sequence_frames = dict()
        self.thread = None
        self._end_frame = None
        self._start_frame = None

        # Atualizando o buffer
        self._checking_integrity()
        self._mount_sequence()

    def start(self):
        # Função que carrega os frames na "pilha", a mesma so carregara se a stack esiver vazia

        if not self.empty():
            return False

        # Inicalizando a obtenção dos estados possiveis dos frames
        count_frame = self.start_frame()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, count_frame)

        def reader(cap, stack, count_frame, sequence_frames, end_frame, bufferlog):
            # Função responsavel por carregar a stack

            start = time()

            while True:
                ret, frame = cap.read()
                if ret and sequence_frames.get(count_frame):
                    # Deve-se colocar o indice do frame + frame na stack
                    stack.append((count_frame, frame))
                if bufferlog:
                    print(len(stack), count_frame, end_frame)
                if count_frame == end_frame:
                    break
                count_frame += 1

            if self.current_frame != end_frame:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame + 1)

            end = time()
            if bufferlog:
                print(f'\nLidos {len(stack)} em {end - start}s')
                print(f'{len(stack) / (end - start):.2f} FPS')

        # Argumentos para a função reader
        args = (self.cap,
                self.stack,
                count_frame,
                self.sequence_frames,
                self.end_frame(),
                self.bufferlog)
        thread = Thread(target=reader, name=self.name, args=args)
        thread.start()
        self.thread = thread

    def join(self):
        self.thread.join()

    def end_frame(self):
        # Metodo que devolve o ultimo frame a ser empilhado, o mesmo
        # deve ser calculado como _end_frame = current_frame - 1, como
        if self._end_frame is None:
            read_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 1
            if read_frame < 0:
                return None
            self._end_frame = int(read_frame)
        return self._end_frame

    def start_frame(self):
        # Metodo que calcula a posição do primeiro frame a ser lido pela stack
        if self._start_frame is None:
            self._start_frame = int(sorted(list(self.sequence_frames.keys()))[0])
        return self._start_frame

    def current_frame(self):
        # Calcula a posição atual do frame, se a stack estiver vazia, a mesma
        # deve retornar None
        if len(self.stack) == 0:
            return None
        ipdb.set_trace()
        return self.start_frame() + len(self.stack)

    def read(self):
        # Metodo para o comsumo do buffer, retorna None quando a pilha estiver vazia
        if not self.empty():
            return self.stack.pop()
        return None

    # Metodos que simulam alguns metodos do objeto Queue

    def empty(self):
        # Checa se a pilha esta vazia
        return len(self.stack) == 0

    def full(self):
        # Checa se a pilha esta cheia
        return len(self.stack) == self.buffersize

    def put(self, value: tuple[int, ndarray]):
        if self.full():
            _ = self.stack.pop(0)
        self.stack.append(value)

    def get(self):
        return self.read()

    def qsize(self):
        return len(self.stack)

    def maxsize(self):
        return self.buffersize


class VideoControl():
    def __init__(self, seq, *, buffersize=25):
        self.filename = None
        self._lots = seq['lot']
        self.lot = seq['lot'][0]
        self.seq = seq

        # Colocamos na queue todos os frames de um lot a serem lidos, ja no
        # buffer colocamos todos os n frames anteriores lidos, onde n é
        # n = self.buffer.maxsize
        self.queue = Queue
        self.buffer = LifoQueue(maxsize=buffersize)

        self.buffersize = buffersize

    def fills_queue(self):
        queue = Queue()
        [queue.put(value) for value in self.seq[self.lot]]
        return queue

    def monitor_buffer(self):
        ...


if __name__ == '__main__':
    cap = cv2.VideoCapture('src/model.mp4')

    cap.set(cv2.CAP_PROP_POS_FRAMES, 600)
    cap.read()
    buffer = VideoBuffer(cap, list(range(1001)), bufferlog=True, buffersize=25)
    buffer.start()
    print('Inicalizando...')
    buffer.join()
