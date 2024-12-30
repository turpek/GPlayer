from src.frame_mapper import FrameMapper
from cv2 import VideoCapture
from threading import Semaphore
from collections import deque
from src.memento import Caretaker, TrashOriginator
from src.buffer_right import VideoBufferRight
from numpy import ndarray
import ipdb


class Trash():
    def __init__(self, cap: VideoCapture, semaphore: Semaphore, frame_count, buffersize=5, bufferlog=False):
        self.__buffersize = buffersize
        self.__frame_count = frame_count
        self._stack = deque(maxlen=(2 * buffersize))
        self._dframes = dict()
        self._mapping = FrameMapper([], frame_count)
        self._buffer = VideoBufferRight(cap, self._mapping, semaphore, buffersize=buffersize, bufferlog=bufferlog)
        self._state = None
        self.__caretaker = Caretaker()
        self.__originator = TrashOriginator(self._mapping)

    def join(self):
        self._buffer.join()

    def __memento_save(self, frame_id: int) -> None:
        self.__originator.set_state(frame_id)
        self.__caretaker.save(self.__originator)

    def _memento_undo(self):
        self.__caretaker.undo(self.__originator)

    def empty(self) -> bool:
        return len(self._stack) == 0

    def full(self) -> bool:
        return len(self._stack) == self._stack.maxlen

    def move(self, frame_id, frame) -> None:
        if not isinstance(frame, ndarray):
            return None
        elif len(self._stack) == self._stack.maxlen:
            fid = self._stack.popleft()
            del self._dframes[fid]
            self.__memento_save(fid)
        self._stack.append(frame_id)
        self._dframes[frame_id] = frame

    def undo(self) -> tuple[int, ndarray] | None:
        bsize = self._stack.maxlen // 2
        if len(self._stack) == bsize and not self.__caretaker.empty():
            for _ in range(bsize):
                if self.__caretaker.empty():
                    break
                self._memento_undo()
                self._stack.appendleft(self.__originator.get_state())
            self._buffer.run()
            while not self._buffer.is_task_complete():
                fid, frame = self._buffer.get()
                self._mapping.remove(fid)
                self._dframes[fid] = frame
                print("Adicionado: ", fid)
        if not self.empty():
            frame_id = self._stack.pop()
            frame = self._dframes[frame_id]
            del self._dframes[frame_id]
            print('Undo: ', frame_id)
            return frame_id, frame
