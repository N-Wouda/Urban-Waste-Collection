from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

from waste.enums import EventStatus

if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from .Cluster import Cluster
    from .Vehicle import Vehicle


class Event(ABC):
    """
    Event class. Events have a time at which they are fired. See subclasses for
    more detail.
    """

    def __init__(self, time: datetime):
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
        return f"{class_name}(time={self.time}, status={self.status.name})"


class ServiceEvent(Event):
    """
    Service event. This event models a cluster being serviced by a vehicle.
    """

    def __init__(
        self,
        time: datetime,
        duration: timedelta,
        id_route: int,
        cluster: Cluster,
        vehicle: Vehicle,
    ):
        super().__init__(time)

        self.duration = duration
        self.id_route = id_route
        self.cluster = cluster
        self.vehicle = vehicle

        self._num_arrivals: Optional[int] = None
        self._volume: Optional[float] = None

    @property
    def num_arrivals(self) -> int:
        if self.is_sealed():
            assert self._num_arrivals is not None
            return self._num_arrivals

        return self.cluster.num_arrivals

    @property
    def volume(self) -> float:
        if self.is_sealed():
            assert self._volume is not None
            return self._volume

        return self.cluster.volume

    def seal(self):
        if self.is_sealed():  # then this is a no-op
            return

        super().seal()
        self._num_arrivals = self.cluster.num_arrivals
        self._volume = self.cluster.volume


class ArrivalEvent(Event):
    """
    Arrival event. This event models a deposit at a cluster.
    """

    def __init__(self, time: datetime, cluster: Cluster, volume: float):
        super().__init__(time)
        self.cluster = cluster
        self.volume = volume


class ShiftPlanEvent(Event):
    """
    Shift plan event. This event models the planning of a shift.
    """

    def __init__(self, time: datetime):
        super().__init__(time)


class BreakEvent(Event):
    """
    Break event. This event models a driver (of the given vehicle) taking
    a break of the given duration back at the depot.
    """

    def __init__(
        self,
        time: datetime,
        duration: timedelta,
        id_route: int,
        vehicle: Vehicle,
    ):
        super().__init__(time)

        self.duration = duration
        self.id_route = id_route
        self.vehicle = vehicle
