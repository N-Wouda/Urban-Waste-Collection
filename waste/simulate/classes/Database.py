import sqlite3

from .Container import Container
from .Result import Result
from .Vehicle import Vehicle


class Database:
    def __init__(self, src_db: str, res_db: str):
        self.read = sqlite3.connect(src_db)
        self.write = sqlite3.connect(res_db)

    def get_containers(self) -> list[Container]:
        return []

    def get_vehicles(self) -> list[Vehicle]:
        return []

    def store(self, res: Result):
        pass

    def __del__(self):
        self.read.close()
        self.write.close()
