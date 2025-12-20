from abc import ABC, abstractmethod
from gplayer.utils import KeyModifierState
from pynput import keyboard
import cv2

class InputHandler(ABC):
    SHIFT_BIT = 0x200  # 512
    ALT_BIT   = 0x400  # 1024

    def __init__(self):
        ...

    def join(self):
        ...

    @abstractmethod
    def get_code(self, delay: int):
        ...


class CV2KeyReader(InputHandler):
    def __init__(self):
        super().__init__()

    def get_code(self, delay: int) -> int:
        return cv2.waitKeyEx(delay)


class HybridKeyReader(InputHandler):
    def __init__(self):
        super().__init__()

        self.__modifiers = KeyModifierState()
        self.__listener = keyboard.Listener(
            on_press=self.__modifiers.on_press,
            on_release=self.__modifiers.on_release
        )

        self.__listener.start()

    def join(self):
        if self.__listener.running:
            self.__listener.stop()
        self.__listener.join()

    def get_code(self, delay: int) -> int:
        code = cv2.waitKeyEx(delay)
        shift, alt = self.__modifiers.snapshot()
        if code != -1:
            code &= 0xFF
            if shift:
                code |= self.SHIFT_BIT
            if alt:
                code |= self.ALT_BIT

        return code
