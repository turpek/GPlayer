from abc import ABC, abstractmethod
from src.player_control import PlayerControl


class Command(ABC):
    @abstractmethod
    def executor(self):
        ...


class PauseCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.set_pause()


class RewindCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.rewind()


class ProceesCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.proceed()


class QuitCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.set_quit()


class IncreaseSpeedCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.increase_speed()


class DecreaseSpeedCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.decrease_speed()


class PauseDelayCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.pause_delay()


class Invoker:
    def __init__(self):
        self.commands = {}

    def set_command(self, key, command: Command) -> None:
        self.commands[key] = command

    def executor_command(self, key) -> None:
        if key in self.commands:
            self.commands[key].executor()
