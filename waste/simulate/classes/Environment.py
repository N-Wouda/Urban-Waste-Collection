import heapq
import logging

from .Container import Container
from .Event import Event, EventType
from .Strategy import Strategy
from .Vehicle import Vehicle

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


class Environment:
    def __init__(self, containers: list[Container], vehicles: list[Vehicle]):
        self.containers = containers
        self.vehicles = vehicles

    def simulate(self, horizon: int, strategy: Strategy):
        """
        Applies the given strategy for a simulation lasting horizon hours.
        """
        queue = _EventQueue()

        # We sample all arrival events once at the start of the simulation.
        # This is good for performance because sampling crosses the C/Python
        # barrier, and can be a bit slow.
        for container in self.containers:
            for event in container.arrivals_until(horizon):
                queue.add(event)

        # Insert the shift planning moments over the time horizon.
        for hour in range(horizon):
            if hour % 24 in [6, 12]:  # TODO config
                queue.add(Event(hour, EventType.SHIFT_PLAN))

        # TODO track statistics

        time = 0.0

        while queue and time <= horizon:
            event = queue.pop()
            time = event.time

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
