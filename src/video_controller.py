from loguru import logger
from src.player_control import PlayerControl
from src.frame_mapper import FrameMapper
from src.trash import Trash
from src.playlist import Playlist
from numpy import ndarray


class VideoController:
    def __init__(self,
                 player: PlayerControl,
                 mapper: FrameMapper,
                 trash: Trash,
                 playlist: Playlist):
        self.__player = player
        self.__mapper = mapper
        self.__trash = trash
        self.__playlist = playlist

    def set_pause(self):
        self.__player.set_pause()

    def rewind(self):
        self.__player.rewind()
        self.__player.set_read()

    def proceed(self):
        self.__player.proceed()
        self.__player.set_read()

    def set_quit(self):
        self.__player.set_quit()

    def increase_speed(self):
        self.__player.increase_speed()

    def decrease_speed(self):
        self.__player.decrease_speed()

    def pause_delay(self):
        self.__player.pause_delay()
        self.__player.disable_collect()

    def restore_delay(self):
        self.__player.restore_delay()

    def remove_frame(self):
        if isinstance(self.__player.frame_id, int):
            swap_buffer = self.__player.servant.is_task_complete()

            frame_id, frame = self.__player.remove_frame()
            self.__mapper.remove(frame_id)
            self.__trash.move(frame_id, frame)
            logger.debug(f'removido {frame_id}')

            # O swap do buffer deve ocorrer quando o frame a ser removido estiver em alguma das
            # extremidades (inicio ou final do vídeo) e o buffer estiver na direção da extremidade
            # em questão, pois ao remover tal frame, o servant passa a ficar vazio, e sua task deve,
            # ser iniciada na proxima leitura, onde start_frame == end_frame, que no caso é igual ao
            # primeiro frame_id no buffer master, assim ocorrendo um duplicação de frames.
            if swap_buffer:
                self.__player.swap()
        else:
            # Criar um erro personalizado aqui
            ...
        self.__player.set_read()

    def undo(self):
        frame_id, frame = self.__trash.undo()
        if isinstance(frame, ndarray):
            self.__mapper.add(frame_id)
            self.__player.restore_frame(frame_id, frame)
            self.__player.undo_config()
            logger.info(f'frame {frame_id} restored')
        else:
            logger.debug('unable to undo removal')

    def next_video(self):
        if not self.__playlist.is_end():
            self.__player.join()
            self.__playlist.next_video(self.__player)
            logger.info(f'next_video: {self.__playlist.video_name()}')
        else:
            logger.debug("it's already at the end of the playlist")

    def prev_video(self):
        if not self.__playlist.is_beginning():
            self.__player.join()
            self.__playlist.prev_video(self.__player)
            logger.info(f'prev_video: {self.__playlist.video_name()}')
        else:
            logger.debug('is already at the beginning of the playlist')

    def read(self):
        return self.__player.read()

    def quit(self):
        return self.__player.quit()

    def set_frame(self, frame_id: int):
        self.__player.servant.set(frame_id)
        self.__player.master.set(frame_id)
        # self.__player.servant.run()

    def join(self):
        self.__player.master.join()
        self.__player.servant.join()
        self.__player.trash.join()

    @property
    def frame_id(self):
        return self.__player.frame_id
