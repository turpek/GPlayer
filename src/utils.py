from __future__ import annotations
from collections import deque
from src.custom_exceptions import FrameWrapperError, SimpleStackError
from src.interfaces import IMementoHandler
from src.memento import Caretaker
from numpy import ndarray
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.section import VideoSection
    from src.memento import TrashOriginator, SectionOriginator
    from src.trash import Trash


class SimpleStack:

    def __init__(self, stack_type):
        self.__stack = deque()
        self.__stack_type = stack_type

    def __len__(self):
        return len(self.__stack)

    def empty(self):
        return len(self.__stack) == 0

    def push(self, item):

        if not isinstance(item, self.__stack_type):
            raise TypeError(
                f'Expected type "{self.__stack_type.__name__}", '
                f'but received "{type(item).__name__}".'
            )
        self.__stack.append(item)

    @property
    def top(self):
        if not self.empty():
            return self.__stack[-1]

    def pop(self):
        if self.empty():
            raise SimpleStackError("Pop failed: Stack is empty.")
        return self.__stack.pop()


class FrameMementoHandler(IMementoHandler):
    def __init__(self, originator: TrashOriginator, caretaker: Caretaker, trash: Trash = None):
        self.__caretaker = caretaker
        self.__originator = originator
        self.__trash = trash

    def store_mementos(self, section: VideoSection):
        removed_frames = section.get_trash()
        while self.__caretaker.undo(self.__originator):
            removed_frames.append(self.__originator.get_state())
        # frames_id = deque()
        # removed_frames = section.get_trash()
        # while self.__caretaker.can_undo():
        #     self.__caretaker.undo(self.__originator)
        #     frames_id.append(self.__originator.get_state())

        # while self.__trash.can_undo():
        #     frames_id.appendleft(self.__trash._stack.popleft())
        # while len(frames_id):
        #     removed_frames.append(frames_id.popleft())

    def load_mementos(self, section: VideoSection):
        removed_frames = section.get_trash()
        while len(removed_frames) > 0:
            self.__originator.set_state(removed_frames.pop())
            self.__caretaker.save(self.__originator)


class SectionMementoHandler(IMementoHandler):
    def __init__(self, originator: SectionOriginator, caretaker: Caretaker):
        self.__caretaker = caretaker
        self.__originator = originator

    def store_mementos(self, removed_sections: SimpleStack):
        while self.__caretaker.undo(self.__originator):
            removed_sections.push(self.__originator.get_state())

    def load_mementos(self, removed_sections: SimpleStack):
        while not removed_sections.empty():
            self.__originator.set_state(removed_sections.pop())
            self.__caretaker.save(self.__originator)


class FrameWrapper:
    def __init__(self, frame_id: int, frame: ndarray = None):
        self.__frame_id = frame_id
        self.__frame = frame

    def __repr__(self):
        return f"FrameWrapper('{self.__frame_id}')"

    def __eq__(self, obj: FrameWrapper | int) -> bool:
        if isinstance(obj, FrameWrapper):
            return self.id_ == obj.id_
        return self.id_ == obj

    def __lt__(self, obj: FrameWrapper | int) -> bool:
        if isinstance(obj, FrameWrapper):
            return self.id_ < obj.id_
        return self.id_ < obj

    def set_frame(self, frame: ndarray) -> None:
        if isinstance(self.__frame, ndarray):
            raise FrameWrapperError("frame is already defined")
        self.__frame = frame

    @property
    def id_(self):
        return self.__frame_id

    def get_frame(self):
        return self.__frame


class FrameStack:
    def __init__(self, maxlen):
        self.__stack = deque(maxlen=maxlen)
        self.__maxlen = maxlen

    def __len__(self):
        return len(self.__stack)

    @property
    def maxlen(self):
        return self.__maxlen

    def empty(self):
        return len(self) == 0

    def pop(self) -> tuple[int, ndarray]:
        return self.__stack.pop()

    def push(self, frame: FrameWrapper) -> None:
        self.__stack.append(frame)

    def can_update_memento(self, trash: Trash) -> bool:
        return trash.can_undo() and len(self) <= self.maxlen // 2

    def _check_update_memento(self, trash: Trash) -> bool:
        return trash.can_undo() and len(self) < self.maxlen

    def _memento_save(self, list_frames: list, trash: Trash) -> None:
        while len(list_frames) > 0:
            trash._memento_save(list_frames.pop())

    def _create_wrapper(self, frame_id: int) -> FrameWrapper:
        frame = FrameWrapper(frame_id, None)
        self.__stack.appendleft(frame)
        return frame

    def update_mementos(self, trash: Trash):
        frames_map = {}
        if self.can_update_memento(trash):
            temp = []
            while self._check_update_memento(trash):
                frame_id = trash._memento_undo()
                temp.append(frame_id)
                if frame_id not in self.__stack:
                    frames_map[frame_id] = self._create_wrapper(frame_id)
                print(frame_id)
            self._memento_save(temp, trash)
        return frames_map
