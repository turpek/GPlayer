from collections import deque
from src.frame_mapper import FrameMapper
from src.interfaces import IMemento, IOriginator


class TrashMemento(IMemento):
    def __init__(self, state: int):
        self._state = state

    def get_state(self) -> int:
        return self._state


class TrashOriginator(IOriginator):
    def __init__(self, mapping: FrameMapper):
        self.__state = None
        self.__mapping = mapping

    def set_state(self, state: int):
        self.__state = state

    def save(self) -> TrashMemento:
        return TrashMemento(self.__state)

    def undo(self, memento: TrashMemento) -> None:
        self.__state = memento.get_state()
        self.__mapping.add(self.__state)

    def get_state(self) -> int:
        return self.__state


class Caretaker:

    def __init__(self):
        self._mementos = deque()

    def can_undo(self) -> bool:
        return len(self._mementos) > 0

    def save(self, originator: IOriginator) -> None:
        self._mementos.append(originator.save())

    def undo(self, originator: IOriginator):
        if self.can_undo():
            memento = self._mementos.pop()
            originator.undo(memento)
            return True
        return False
