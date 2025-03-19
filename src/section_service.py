from src.template import TemplateFactory, SectionManagerProcessFactory
from src.adapter import JSONSectionManagerAdapter
from src.section import SectionManager
from pathlib import Path


class SectionService:
    @staticmethod
    def load_section_manager(
        file_path: Path,
        label: str,
        frame_count: int
    ) -> SectionManager:
        try:
            data_secman = SectionManagerProcessFactory.create_process(
                file_path, label
            )
            section_manager_process = JSONSectionManagerAdapter(data_secman[label])
            return SectionManager(section_manager_process)
        except FileNotFoundError:
            template = TemplateFactory.save_template(file_path, label, frame_count)
            print(f"Arquivo {file_path} não encontrado. Um template foi criado.")

            suffix = file_path.suffix
            if suffix == '.json':
                section_manager_process = JSONSectionManagerAdapter(template[label])

            return SectionManager(section_manager_process)
