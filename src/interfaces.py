from abc import ABC, abstractmethod
from collections import deque


class IVideoBuffer(ABC):

    def __init__(self):
        ...

    @abstractmethod
    def set_frame_id(self) -> None:
        ...


class IFakeVideoBuffer(IVideoBuffer):

    def __init__(self):
        ...

    def set_frame_id(self) -> None:
        ...


class IMemento(ABC):
    @abstractmethod
    def get_state(self) -> int:
        ...


class IOriginator(ABC):
    @abstractmethod
    def save(self) -> IMemento:
        ...

    @abstractmethod
    def undo(self, memento: IMemento):
        ...


class IMementoHandler(ABC):

    @abstractmethod
    def export_mementos(self, originator: IOriginator):
        ...

    @abstractmethod
    def import_mementos(self, originator: IOriginator):
        ...


class Command(ABC):
    @abstractmethod
    def executor(self):
        ...


class ISectionAdapter(ABC):
    @abstractmethod
    def start(self) -> int:
        ...

    @abstractmethod
    def end(self) -> int:
        ...

    @abstractmethod
    def removed_frames(self) -> deque:
        ...

    @abstractmethod
    def black_list_frames(self) -> list:
        ...


