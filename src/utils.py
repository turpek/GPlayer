from __future__ import annotations
from collections import deque
from src.custom_exceptions import SimpleStackError
from src.interfaces import IMementoHandler
from src.memento import Caretaker

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.section import Section
    from src.memento import TrashOriginator


class SimpleStack:

    def __init__(self, stack_type):
        self.__stack = deque()
        self.__stack_type = stack_type

    def empty(self):
        return len(self.__stack) == 0

    def push(self, item):

        if not isinstance(item, self.__stack_type):
            raise TypeError(
                f'Expected type "{self.__stack_type.__name__}", '
                f'but received "{type(item).__name__}".'
            )
        self.__stack.append(item)

    def top(self):
        if not self.empty():
            return self.__stack[-1]

    def pop(self):
        if self.empty():
            raise SimpleStackError("Pop failed: Stack is empty.")
        return self.__stack.pop()


class SectionMementoHandler(IMementoHandler):
    def __init__(self, originator: TrashOriginator, caretaker: Caretaker):
        self.__caretaker = caretaker
        self.__originator = originator

    def store_mementos(self, section: Section):
        removed_frames = section.get_trash()
        while self.__caretaker.undo(self.__originator):
            removed_frames.append(self.__originator.get_state())

    def load_mementos(self, section: Section):
        removed_frames = section.get_trash()
        while len(removed_frames) > 0:
            self.__originator.set_state(removed_frames.pop())
            self.__caretaker.save(self.__originator)
