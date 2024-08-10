from src.buffer import VideoBufferLeft, VideoBufferRight
from queue import Queue, LifoQueue
from time import sleep

import cv2
import ipdb


class Control():
    def __init__(self, sequence: dict, *, buffersize=25, bufferlog=False):
        self.sequence = sequence
        self.buffersize = buffersize
        self.bufferlog = bufferlog

        self.filename = sequence['filename']
        self.start_frame = sequence['start_frame']
        self.end_frame = sequence['end_frame']
        self._lots = sequence['lot']
        self._lot = self._lots.pop(0)

        self.right_lots = Queue()
        self.left_lots = LifoQueue()
        [self.right_lots.put(lo) for lo in self._lots]

        # Variavel usada no metodo undo, deve receber uma tupla, onde
        # story -> (str[lot], int[index], frame_id)
        self.story = Queue()

        self.index = 0

        self.cap = cv2.VideoCapture(self.filename)
        self.cap1 = cv2.VideoCapture(self.filename)

        self.__check_integraty()

        # Colocando o objeto cap no primeiro frame do lote e lendo-o
        # pois por padrão VideoBufferLeft trabalha com o frame atual,
        # se o mesmo não for lido, então o estado é indeterminado
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_id())
        self.ret, self._frame = self.cap.read()

        self.bufferRight = VideoBufferRight(self.cap, self.frames_id(), buffersize=buffersize, bufferlog=bufferlog, name='Buffer1')
        self.bufferRight.start()
        self.bufferLeft = VideoBufferLeft(self.cap, self.frames_id(), buffersize=buffersize, bufferlog=bufferlog, name='Buffer0')
        self.aux_buffer = True

    def __check_integraty(self):
        if not self.cap.isOpened():
            raise Exception('Não foi possível abrir o vídeo')

    def frame(self):
        if self._frame is not None:
            return self._frame

    def lot(self):
        return self._lot

    def next_lot(self):
        if self.right_lots.empty():
            return False
        self.left_lots.put(self._lot)
        self._lot = self.right_lots.get()
        return True

    def prev_lot(self):
        if self.left_lots.empty():
            return False
        self.right_lots.put(self._lot)
        self._lot = self.left_lots.get()
        return True

    def frames_id(self):
        lot = self._lot
        return self.sequence[lot]

    def frame_id(self):
        lot = self._lot
        if len(self.sequence[lot]) == 0:
            raise IndexError('a sequencia está vazia!')
        return self.sequence[lot][self.index]

    def next_frame(self):
        # tempo necessario para o buffer ler 1 frame!
        lot = self._lot
        is_dead = not self.bufferRight.thread.is_alive()
        if len(self.sequence[lot]) - 1 > self.index:

            if self.bufferRight.empty() and is_dead:
                # Se o buffer right estiver vazio devemos ler o proximo frame
                # de maneira manual e atualizar os dados no frame e enchelo novamente

                # Colocando o frame atual no buffer da esquerda
                self.bufferLeft.put((self.frame_id(), self.frame()))

                # Lendo o proximo frame
                self.index += 1
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_id())
                self.ret, self._frame = self.cap.read()

                # Atualizando o buffer
                self.bufferRight.reflesh(self.frames_id())
                self.bufferRight.start()
                return True
            else:
                self.bufferLeft.put((self.frame_id(), self.frame()))
                if self.bufferRight.observer(self.frame_id()):
                    frame_id, self._frame = self.bufferRight.read()
                    self.index += 1
                else:
                    raise Exception(f'Não foi possível ler o frame do buffer {self.bufferRight.name}')
                return True
        return False

    def prev_frame(self):
        if self.index == 0:
            return False
        if self.bufferLeft.empty():
            self.bufferLeft = self.aux_buffer
            self.aux_buffer = True
            """
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_id())
            ret, frame_id = self.cap.read()
            self.bufferLeft = VideoBufferLeft(self.cap,
                                              self.frames_id(),
                                              buffersize=self.buffersize,
                                              bufferlog=self.bufferlog,
                                              name='Buffer2')
            self.bufferLeft.start()
            self.bufferLeft.join()
            """
        if not self.bufferLeft.empty() and self.index > 0:
            self.bufferRight.put((self.frame_id(), self.frame()))
            frame_id, self._frame = self.bufferLeft.read()
            self.index -= 1

            start_frame = frame_id - self.buffersize + 1
            if self.aux_buffer is True and start_frame > self.start_frame:
                self.cap1.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                _ = self.cap1.read()
                self.aux_buffer = VideoBufferLeft(self.cap1,
                                                  self.frames_id(),
                                                  buffersize=self.buffersize,
                                                  bufferlog=True,
                                                  name='Buffer3')
                self.aux_buffer.start()
            return True

    def remove_frame(self):
        lot = self._lot
        if len(self.sequence[lot]) == 0:
            return False

        index = self.index
        frame_id = self.sequence[lot].pop(index)
        self.story.put((lot, index, frame_id))
        return True
