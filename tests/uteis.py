import numpy as np
import cv2


class MyVideoCapture():
    def __init__(self, isopened=True):
        self.frames = [np.zeros((2, 2)) for x in range(500)]
        self.index = 0
        self.isopened = isopened

    def read(self):
        if self.index < len(self.frames):
            frame = self.frames[self.index]
            self.index += 1
            return True, frame
        return False, None

    def grab(self):
        self.index += 1

    def set(self, flag, value):
        if cv2.CAP_PROP_POS_FRAMES == flag:
            if len(self.frames) >= value and value >= 0:
                self.index = value
                return True
            else:
                return False
        return False

    def get(self, flag):
        if cv2.CAP_PROP_FRAME_COUNT == flag:
            return len(self.frames)
        elif cv2.CAP_PROP_POS_FRAMES == flag:
            return self.index
        elif cv2.CAP_PROP_FPS == flag:
            return 24
        return False

    def isOpened(self):
        return self.isopened

    def release(self):
        self.isopened = False
        ...
