from __future__ import annotations

import heapq
import logging
from itertools import count
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np

from waste.constants import HOURS_IN_DAY, SHIFT_PLAN_TIME, TIME_PER_CONTAINER

from .Container import Container
from .Event import ArrivalEvent, Event, ServiceEvent, ShiftPlanEvent
from .Route import Route
from .Vehicle import Vehicle

if TYPE_CHECKING:
    from waste.strategies import Strategy

logger = logging.getLogger(__name__)


class _EventQueue:
    """
    Simple internal event queue that efficiently manages events in order of
    time.
    """

    def __init__(self):
        self._events: list[tuple[float, int, Event]] = []
        self._counter = count(0)

    def add(self, event: Event):
        tiebreaker = next(self._counter)
        heapq.heappush(self._events, (event.time, tiebreaker, event))

    def __len__(self) -> int:
        return len(self._events)

    def pop(self) -> Event:
        *_, event = heapq.heappop(self._events)
        return event


class Simulator:
    """
    The simulator class. This class is responsible for running the main
    simulation event queue, and has a few attributes that describe the
    simulation environment.
    """

    def __init__(
        self,
        distances: np.array,
        durations: np.array,
        containers: list[Container],
        vehicles: list[Vehicle],
    ):
        self.distances = distances
        self.durations = durations
        self.containers = containers
        self.vehicles = vehicles

    def __call__(
        self,
        horizon: int,
        store: Callable[[Event | Route], Optional[int]],
        strategy: Strategy,
    ):
        """
        Applies the given strategy for a simulation lasting horizon hours.
        """
        queue = _EventQueue()

        # Insert all arrival events into the event queue. This is the only
        # source of uncertainty in the simulation.
        for container in self.containers:
            for arrival in container.arrivals_until(horizon):
                queue.add(arrival)

        # Insert the shift planning moments into the event queue.
        for day in range(0, horizon, HOURS_IN_DAY):
            if day + SHIFT_PLAN_TIME <= horizon:
                queue.add(ShiftPlanEvent(day + SHIFT_PLAN_TIME))

        time = 0.0

        while queue and time <= horizon:
            event = queue.pop()

            if event.time >= time:
                time = event.time
            else:
                msg = f"{event} time is before current time {time:.2f}!"
                logger.error(msg)
                raise ValueError(msg)

            # First seal the event. This ensures all data that was previously
            # linked to changing objects is made static at their current
            # values ("sealed"). After sealing, an event's state has become
            # independent from that of the objects it references.
            event.seal()
            store(event)

            if isinstance(event, ArrivalEvent):
                container = event.container
                container.arrive(event.volume)

                logger.debug(f"Arrival at {container.name} at t = {time:.2f}.")
            elif isinstance(event, ServiceEvent):
                container = event.container
                container.service()

                logger.debug(f"Service at {container.name} at t = {time:.2f}.")
            elif isinstance(event, ShiftPlanEvent):
                logger.info(f"Generating shift plan at t = {event.time:.2f}.")
                routes = strategy(self, event)

                for route in routes:
                    id_route = store(route)
                    assert id_route is not None

                    service_time = event.time
                    prev = 0

                    for container_idx in route.plan:
                        service_time += self.durations[prev, container_idx]

                        queue.add(
                            ServiceEvent(
                                service_time,
                                id_route=id_route,
                                container=self.containers[container_idx],
                                vehicle=route.vehicle,
                            )
                        )

                        service_time += TIME_PER_CONTAINER
                        prev = container_idx
            else:
                msg = f"Unhandled event of type {type(event)}."
                logger.error(msg)
                raise ValueError(msg)
