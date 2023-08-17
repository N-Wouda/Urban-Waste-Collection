from __future__ import annotations

import logging
from heapq import heappop, heappush
from itertools import count
from typing import TYPE_CHECKING, Callable, Iterator, Optional

from waste.constants import TIME_PER_CONTAINER

from .Event import (
    ArrivalEvent,
    BreakEvent,
    Event,
    ServiceEvent,
    ShiftPlanEvent,
)

if TYPE_CHECKING:
    import numpy as np
    from numpy.random import Generator

    from waste.strategies import Strategy

    from .Container import Container
    from .Route import Route
    from .Vehicle import Vehicle

logger = logging.getLogger(__name__)


class _EventQueue:
    """
    Simple internal event queue that efficiently manages events in order of
    time.
    """

    def __init__(self):
        self._events = []
        self._counter = count(0)

    def __len__(self) -> int:
        return len(self._events)

    def push(self, event: Event):
        tiebreaker = next(self._counter)
        heappush(self._events, (event.time, tiebreaker, event))

    def pop(self) -> Event:
        *_, event = heappop(self._events)
        return event


class Simulator:
    """
    The simulator class. This class is responsible for running the main
    simulation event queue, and has a few attributes that describe the
    simulation environment.
    """

    def __init__(
        self,
        generator: Generator,
        distances: np.array,
        durations: np.array,
        containers: list[Container],
        vehicles: list[Vehicle],
    ):
        self.generator = generator
        self.distances = distances
        self.durations = durations
        self.containers = containers
        self.vehicles = vehicles

    def __call__(
        self,
        store: Callable[[Event | Route], Optional[int]],
        strategy: Strategy,
        initial_events: list[Event],
    ):
        """
        Applies a strategy for a simulation starting with the given initial
        events.        .
        """
        events = _EventQueue()

        for event in initial_events:
            events.push(event)

        while events:
            event = events.pop()

            # TODO handle break events

            # First seal the event. This ensures all data that was previously
            # linked to changing objects is made static at their current
            # values ("sealed"). After sealing, an event's state has become
            # independent from that of the objects it references.
            event.seal()
            store(event)

            match event:
                case ArrivalEvent(time=time, container=c, volume=vol):
                    logger.debug(f"Arrival at {c.name} at t = {time}.")
                    c.arrive(vol)
                case ServiceEvent(time=time, container=c):
                    logger.debug(f"Service at {c.name} at t = {time}.")
                    c.service()
                case ShiftPlanEvent(time=time):
                    logger.info(f"Generating shift plan at t = {time}.")
                    for event in self._plan_shift(store, strategy, event):
                        events.push(event)
                case _:
                    msg = f"Unhandled event of type {type(event)}."
                    logger.error(msg)
                    raise ValueError(msg)

    def _plan_shift(
        self,
        store: Callable[[Event | Route], Optional[int]],
        strategy: Strategy,
        event: ShiftPlanEvent,
    ) -> Iterator[ServiceEvent | BreakEvent]:
        for route in strategy(self, event):
            id_route = store(route)
            assert id_route is not None

            service_time = route.start_time
            prev = 0  # start from depot

            for container_idx in route.plan:
                idx = container_idx + 1  # + 1 because 0 is depot
                service_time += self.durations[prev, idx].item()

                # TODO yield breaks

                yield ServiceEvent(
                    service_time,
                    id_route=id_route,
                    container=self.containers[container_idx],
                    vehicle=route.vehicle,
                )

                service_time += TIME_PER_CONTAINER
                prev = idx
