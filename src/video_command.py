from abc import ABC, abstractmethod
from loguru import logger
from numpy import ndarray
from src.player_control import PlayerControl
from src.frame_mapper import FrameMapper
from src.video_buffer import IVideoBuffer
from src.buffer_left import VideoBufferLeft
from src.buffer_right import VideoBufferRight
from src.trash import Trash
import ipdb


class FrameRemoveOrchestrator:
    def __init__(self, player_control: PlayerControl, frame_mapper: FrameMapper, trash: Trash):
        self.player_control = player_control
        self.frame_mapper = frame_mapper
        self.trash = trash

    def remove(self):
        player_control = self.player_control
        if isinstance(player_control.frame_id, int):
            swap_buffer = player_control.servant.is_task_complete()
            frame_id, frame = player_control.remove_frame()

            print(f'frame_id {frame_id}')
            self.frame_mapper.remove(frame_id)
            self.trash.move(frame_id, frame)
            logger.debug(f'removido {frame_id}')

            # O swap do buffer deve ocorrer quando o frame a ser removido estiver em alguma das
            # extremidades (inicio ou final do vídeo) e o buffer estiver na direção da extremidade
            # em questão, pois ao remover tal frame, o servant passa a ficar vazio, e sua task deve,
            # ser iniciada na proxima leitura, onde start_frame == end_frame, que no caso é igual ao
            # primeiro frame_id no buffer master, assim ocorrendo um duplicação de frames.
            if swap_buffer:
                # ipdb.set_trace()
                player_control.servant, player_control.master = player_control.master, player_control.servant
        else:
            # Criar um erro personalizado aqui
            ...


class FrameUndoOrchestrator:
    def __init__(self, player_control: PlayerControl, frame_mapper: FrameMapper, trash: Trash):
        self.player_control = player_control
        self.frame_mapper = frame_mapper
        self.trash = trash

    def _goto_frame(self, frame_id: int, player: PlayerControl, buffer: IVideoBuffer) -> None:
        if isinstance(buffer, VideoBufferRight):
            while frame_id > player.frame_id:
                player.read()

    def undo(self):
        frame_id, frame = self.trash.undo()
        if isinstance(frame, ndarray):
            servant = self.player_control.servant
            master = self.player_control.master
            # if farme_id > servant._buffer[0]
            self._goto_frame(frame_id, self.player_control, servant)
            master


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


class RemoveFrameCommand(Command):
    def __init__(self, receiver: FrameRemoveOrchestrator):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.remove()


class Invoker:
    def __init__(self):
        self.commands = {}

    def set_command(self, key, command: Command) -> None:
        self.commands[key] = command

    def executor_command(self, key) -> None:
        if key in self.commands:
            self.commands[key].executor()
