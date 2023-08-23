from dataclasses import dataclass
from datetime import datetime

from .Vehicle import Vehicle


@dataclass
class Route:
    plan: list[int]  # visited containers (indices starting at 0); depot -1
    vehicle: Vehicle
    start_time: datetime

    def __len__(self) -> int:
        return len(self.plan)
