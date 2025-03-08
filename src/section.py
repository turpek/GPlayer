from collections import deque
from queue import LifoQueue, Queue
from src.frame_mapper import FrameMapper
from src.trash import Trash

# Indice para fazer a leitura do dicionario da seção
SECTION_IDS = 'SECTION_IDS'
REMOVED_FRAMES = 'REMOVED_FRAMES'
START_FRAME = 0  # Indice para a leitura da tupla do range de frames
END_FRAME = 1  # Indice para a leitura da tupla do range de frames
RANGE_FRAMES = 'RANGE_FRAME_ID'
REMOVED_FRAMES = 'REMOVED_FRAMES'


class VideoSection:
    def __init__(self, section: dict):
        self.start_frame = section[RANGE_FRAMES][START_FRAME]
        self.end_frame = section[RANGE_FRAMES][END_FRAME]
        self.removed_frames = deque(section[REMOVED_FRAMES])

    def set_range_frames(self, frame_mapper: FrameMapper):
        self.start_frame = frame_mapper[0]
        self.end_frame = frame_mapper[-1]

    def get_deque(self) -> deque:
        self.removed_frames = deque()
        return self.removed_frames


class ManagerSection:
    def __init__(self, sections: dict):

        # Carregandos os ids de seção na fila
        right_section = Queue()
        [right_section.put(sid) for sid in sections[SECTION_IDS]]

        self.__right_section = right_section
        self.__left_section = LifoQueue()
        self.__current_section = self.__right_section.get()
        self.__sections = dict()
        self.__load_sections(sections)

    def __load_sections(self, sections):
        for sid in sections[SECTION_IDS]:
            self.__sections[sid] = VideoSection(sections[sid])

    @property
    def current_id(self) -> int:
        """Retorna o id da seção atual."""
        return self.__current_section

    def export_frames_id(self, trash: Trash):
        """Exporta os frames id excluídos para uma possível restauração futura."""
        trash.export_frames_id(self.__sections[self.current_id].get_deque())

    def save_data(self, frame_mapper: FrameMapper, trash: Trash):
        """Salva os dados """
        self.__sections[self.current_id].set_range_frames(frame_mapper)
        self.export_frames_id(trash)

    def next_section(self, player, frame_mapper: FrameMapper, trash: Trash):
        if not self.__right_section.empty():
            self.save_data(frame_mapper, trash)
            self.__left_section.put(self.current_id)
            self.__current_section = self.__right_section.get()
