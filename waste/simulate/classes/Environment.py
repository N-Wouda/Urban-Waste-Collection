import heapq
import logging

from .Container import Container
from .Event import Event
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

        _info(self, f"There are {len(events)} arrivals in queue.")

        while events and self.time <= horizon:
            self.time, event = heapq.heappop(events)
            _info(self, f"Handling {event}.")

            for event in strategy(self, event):
                _debug(self, f"Adding event {event}.")
                heapq.heappush(events, (event.time, event))


def _debug(env: Environment, msg: str):
    logger.debug(f"[t = {env.time}] {msg}")


def _info(env: Environment, msg: str):
    logger.info(f"[t = {env.time}] {msg}")
