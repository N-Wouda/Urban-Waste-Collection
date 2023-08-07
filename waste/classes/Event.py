from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

from waste.enums import EventStatus

if TYPE_CHECKING:
    from .Container import Container
    from .Vehicle import Vehicle


class Event(ABC):
    """
    Event class. Events have a time at which they are fired. See subclasses for
    more detail.
    """

    def __init__(self, time: float):
        self.time = time
        self.status = EventStatus.PENDING

    def is_pending(self) -> bool:
        return self.status == EventStatus.PENDING

    def is_sealed(self) -> bool:
        return self.status == EventStatus.SEALED

    def seal(self):
        self.status = EventStatus.SEALED

    def __str__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(time={self.time:.2f}, status={self.status.name})"

    def __lt__(self, other):
        return self.time < other.time


class ServiceEvent(Event):
    """
    Service event. This event models a container being serviced by a vehicle.
    """

    def __init__(
        self,
        time: float,
        id_route: int,
        container: Container,
        vehicle: Vehicle,
    ):
        super().__init__(time)

        self.id_route = id_route
        self.container = container
        self.vehicle = vehicle

        self._num_arrivals: Optional[int] = None
        self._volume: Optional[float] = None

    @property
    def num_arrivals(self) -> int:
        if self.is_sealed():
            assert self._num_arrivals is not None
            return self._num_arrivals

        return self.container.num_arrivals

    @property
    def volume(self) -> float:
        if self.is_sealed():
            assert self._volume is not None
            return self._volume

        return self.container.volume

    def seal(self):
        super().seal()

        self._num_arrivals = self.container.num_arrivals
        self._volume = self.container.volume


class ArrivalEvent(Event):
    """
    Arrival event. This event models a deposit at a container.
    """

    def __init__(self, time: float, container: Container, volume: float):
        super().__init__(time)
        self.container = container
        self.volume = volume


class ShiftPlanEvent(Event):
    """
    Shift plan event. This event models the planning of a shift.
    """

    def __init__(self, time: float):
        super().__init__(time)
