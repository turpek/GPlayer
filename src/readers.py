import json
from pathlib import Path
from src.interfaces import IDataReader


class JSONReader(IDataReader):

    @staticmethod
    def read(file_path: Path):
        with open(file_path, 'r') as file:
            return json.load(file)
