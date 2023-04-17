from dataclasses import dataclass

from waste.enums import EventType

from .Container import Container
from .Event import Event
from .Vehicle import Vehicle


@dataclass
class Route:
    plan: list[tuple[float, Container]]  # list of (service time, Container)
    vehicle: Vehicle

    def services(self) -> list[Event]:
        return [
            Event(
                time,
                EventType.SERVICE,
                container=container,
                vehicle=self.vehicle,
            )
            for time, container in self.plan
        ]
