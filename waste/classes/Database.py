import sqlite3
from collections import defaultdict

import numpy as np

from .Container import Container
from .Result import Result
from .Vehicle import Vehicle


class Database:
    def __init__(self, src_db: str, res_db: str):
        self.read = sqlite3.connect(src_db)
        self.write = sqlite3.connect(res_db)

    def containers(self) -> list[Container]:
        sql = """-- sql
            SELECT cr.container,
                   1000 * c.capacity,  -- in liters
                   cr.hour,
                   cr.rate
            FROM container_rates AS cr
                    INNER JOIN containers AS c
                                ON c.container = cr.container
            ORDER BY cr.container, cr.hour;
        """
        capacities: dict[str, float] = {}
        rates: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(24))
        for name, capacity, hour, rate in self.read.execute(sql):
            capacities[name] = capacity
            rates[name][hour] = rate

        return [
            Container(name=name, rates=rates[name], capacity=capacity)
            for name, capacity in capacities.items()
        ]

    def vehicles(self) -> list[Vehicle]:
        return []  # TODO

    def store(self, res: Result):
        pass  # TODO

    def __del__(self):
        self.read.close()
        self.write.close()
