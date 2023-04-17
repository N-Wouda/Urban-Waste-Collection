from dataclasses import dataclass

from .Container import Container
from .Vehicle import Vehicle


@dataclass
class Route:
    plan: list[tuple[float, Container]]  # list of (service time, Container)
    vehicle: Vehicle
