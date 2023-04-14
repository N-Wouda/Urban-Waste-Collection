import heapq
import logging

from .Container import Container
from .Event import Event, EventType
from .Strategy import Strategy
from .Vehicle import Vehicle

logger = logging.getLogger(__name__)


class Environment:
    def __init__(self, containers: list[Container], vehicles: list[Vehicle]):
        self.containers = containers
        self.vehicles = vehicles
        self.time = 0.0  # hours

    def simulate(self, horizon: int, strategy: Strategy):
        """
        Applies the given strategy for a simulation lasting horizon hours.
        """
        events: list[tuple[float, Event]] = []

        # We sample all arrival events once at the start of the simulation.
        # This is good for performance because sampling crosses the C/Python
        # barrier, and can be a bit slow.
        for container in self.containers:
            for event in container.arrivals_until(horizon):
                heapq.heappush(events, (event.time, event))

        logger.info(f"There are {len(events)} arrivals in queue.")

        # Insert the shift planning moments over the time horizon.
        for hour in range(horizon):
            if hour % 24 in [6, 12]:  # TODO config
                event = Event(hour, EventType.SHIFT_PLAN)
                heapq.heappush(events, (event.time, event))

        # TODO track statistics

        while events and self.time <= horizon:
            self.time, event = heapq.heappop(events)
            logger.debug(f"Handling {event}.")

            if event.type == EventType.ARRIVAL:
                container = event.kwargs["container"]
                container.arrive(event)
            elif event.type == EventType.SERVICE:
                container = event.kwargs["container"]
                container.service()
            elif event.type == EventType.SHIFT_PLAN:
                logger.info(f"Generating shift plan at t = {event.time:.2f}.")

                for event in strategy(self, event):
                    logger.debug(f"Adding event {event}.")
                    heapq.heappush(events, (event.time, event))
            else:
                raise ValueError(f"Unhandled event of type {event.type.name}.")
