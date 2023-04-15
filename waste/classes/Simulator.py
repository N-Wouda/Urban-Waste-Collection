from __future__ import annotations

import heapq
import logging
from typing import TYPE_CHECKING, Callable

from .Container import Container
from .Event import Event, EventType
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
        self._events: list[tuple[float, Event]] = []

    def add(self, event: Event):
        heapq.heappush(self._events, (event.time, event))

    def __len__(self) -> int:
        return len(self._events)

    def pop(self) -> Event:
        _, event = heapq.heappop(self._events)
        return event


class Simulator:
    def __init__(self, containers: list[Container], vehicles: list[Vehicle]):
        self.containers = containers
        self.vehicles = vehicles

    def __call__(
        self,
        horizon: int,
        store: Callable[[Event], None],
        strategy: Strategy,
        shift_plan: list[float],
        volume_range: tuple[float, float],
    ):
        """
        Applies the given strategy for a simulation lasting horizon hours.
        """
        queue = _EventQueue()

        # Insert all arrival events into the event queue. This is the only
        # source of uncertainty in the simulation.
        for container in self.containers:
            for event in container.arrivals_until(horizon, volume_range):
                queue.add(event)

        # Insert the shift planning moments into the event queue.
        for day in range(0, horizon, 24):
            for hour in shift_plan:
                queue.add(Event(day + hour, EventType.SHIFT_PLAN))

        time = 0.0

        while queue and time <= horizon:
            event = queue.pop()
            time = event.time

            store(event)

            if event.type == EventType.ARRIVAL:
                container = event.kwargs["container"]
                container.arrive(event)

                logger.debug(f"Arrival at {container} at t = {time:.2f}.")
            elif event.type == EventType.SERVICE:
                container = event.kwargs["container"]
                container.service()

                logger.info(f"Service at {container} at t = {time:.2f}.")
            elif event.type == EventType.SHIFT_PLAN:
                logger.info(f"Generating shift plan at t = {event.time:.2f}.")

                for event in strategy(self, event):
                    queue.add(event)
            else:
                raise ValueError(f"Unhandled event of type {event.type.name}.")
