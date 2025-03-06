from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from loguru import logger
from numpy import ndarray
from src.player_control import PlayerControl
from src.playlist import Playlist
from src.frame_mapper import FrameMapper
from src.trash import Trash


if TYPE_CHECKING:
    # Para poder usar o `VideoCon` com dica
    from src.video import VideoCon


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
            self.frame_mapper.remove(frame_id)
            self.trash.move(frame_id, frame)
            logger.debug(f'removido {frame_id}')

            # O swap do buffer deve ocorrer quando o frame a ser removido estiver em alguma das
            # extremidades (inicio ou final do vídeo) e o buffer estiver na direção da extremidade
            # em questão, pois ao remover tal frame, o servant passa a ficar vazio, e sua task deve,
            # ser iniciada na proxima leitura, onde start_frame == end_frame, que no caso é igual ao
            # primeiro frame_id no buffer master, assim ocorrendo um duplicação de frames.
            if swap_buffer:
                player_control.servant, player_control.master = player_control.master, player_control.servant
        else:
            # Criar um erro personalizado aqui
            ...


class FrameUndoOrchestrator:
    def __init__(self, player_control: PlayerControl, frame_mapper: FrameMapper, trash: Trash):
        self.player_control = player_control
        self.frame_mapper = frame_mapper
        self.trash = trash

    def undo(self):
        frame_id, frame = self.trash.undo()
        if isinstance(frame, ndarray):
            self.frame_mapper.add(frame_id)
            self.player_control.restore_frame(frame_id, frame)
            logger.info(f'frame {frame_id} restored')
            return True
        else:
            logger.debug('unable to undo removal')

        return False


class NextVideoOrchestrator:
    def __init__(self, video_player: VideoCon, playlist: Playlist):
        self.__video_player = video_player
        self.__playlist = playlist

    def next_video(self):
        if not self.__playlist.is_end():
            self.__video_player.join()
            self.__playlist.next_video(self.__video_player)
            logger.info(f'next_video: {self.__playlist.video_name()}')
        else:
            logger.debug("it's already at the end of the playlist")


class PrevVideoOrchestrator:
    def __init__(self, video_player: VideoCon, playlist: Playlist):
        self.__video_player = video_player
        self.__playlist = playlist

    def prev_video(self):
        if not self.__playlist.is_beginning():
            self.__video_player.join()
            self.__playlist.prev_video(self.__video_player)
            logger.info(f'prev_video: {self.__playlist.video_name()}')
        else:
            logger.debug('is already at the beginning of the playlist')


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
        self.receiver.set_read()


class ProceesCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.proceed()
        self.receiver.set_read()


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
        self.receiver.disable_collect()


class RestoreDelayCommand(Command):
    def __init__(self, receiver: PlayerControl):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.restore_delay()


class RemoveFrameCommand(Command):
    def __init__(self, receiver: FrameRemoveOrchestrator):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.remove()
        self.receiver.player_control.set_read()


class UndoFrameCommand(Command):
    def __init__(self, receiver: FrameUndoOrchestrator):
        self.receiver = receiver

    def executor(self) -> None:
        if self.receiver.undo():
            self.receiver.player_control.disable_collect()
            self.receiver.player_control.disable_update_frame()
            self.receiver.player_control.set_read()


class NextVideoCommand(Command):
    def __init__(self, receiver: NextVideoOrchestrator):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.next_video()


class PrevVideoCommand(Command):
    def __init__(self, receiver: NextVideoOrchestrator):
        self.receiver = receiver

    def executor(self) -> None:
        self.receiver.prev_video()


class Invoker:
    def __init__(self):
        self.commands = {}

    def set_command(self, key, command: Command) -> None:
        self.commands[key] = command

    def executor_command(self, key) -> None:
        if key in self.commands:
            self.commands[key].executor()
