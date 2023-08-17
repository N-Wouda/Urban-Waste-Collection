from dataclasses import dataclass

from .Vehicle import Vehicle


@dataclass
class Route:
    plan: list[int]  # visited container indices
    vehicle: Vehicle

    def __len__(self) -> int:
        return len(self.plan)
