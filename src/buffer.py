from threading import Thread
from queue import LifoQueue
from time import time, sleep
import cv2


class VideoBuffer(Thread):
    def __init__(self, cap, queue, *, name='buffer'):
        super().__init__()
        self.cap = cap
        self.name = name
        self.queue = queue
        self._stoped = False

    def run(self):
        start = time()
        frames = self.queue
        while not self.queue.full():
            ret, frame = self.cap.read()
            print(self.queue.qsize())
            self.queue.put(frame)
        self._stoped = True
        end = time()
        print(f'\nLidos {frames.qsize()} em {end - start}s')
        print(f'{frames.qsize() / (end - start):.2f} FPS')

    def join(self):
        while not self._stoped:
            sleep(0.01)

frames = LifoQueue(maxsize=100)
cap = cv2.VideoCapture('model.mp4')
buffer = VideoBuffer(cap, frames)
buffer.start()


