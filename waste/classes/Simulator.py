from __future__ import annotations

import logging
from heapq import heappop, heappush
from itertools import count
from typing import TYPE_CHECKING, Callable, Iterator, Optional

from .Configuration import Configuration
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
    from .Depot import Depot
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
        logger.debug(f"Adding event {event} to the queue at t = {event.time}.")

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
        depot: Depot,
        distances: np.array,
        durations: np.array,
        containers: list[Container],
        vehicles: list[Vehicle],
        config: Configuration = Configuration(),
    ):
        self.generator = generator
        self.depot = depot
        self.distances = distances
        self.durations = durations
        self.containers = containers
        self.vehicles = vehicles
        self.config = config

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

            # First seal the event. This ensures all data that was previously
            # linked to changing objects is made static at their current
            # values ("sealed"). After sealing, an event's state has become
            # independent from that of the objects it references.
            event.seal()

            # Store the event, and pass it to the strategy so it can do its
            # own thing.
            store(event)
            strategy.observe(event)

            match event:
                case ArrivalEvent(time=time, container=c, volume=vol):
                    logger.debug(f"Arrival at {c.name} at t = {time}.")
                    c.arrive(vol)
                case ServiceEvent(time=time, container=c):
                    logger.debug(f"Service at {c.name} at t = {time}.")
                    c.service()
                case BreakEvent(time=time, vehicle=v):
                    logger.debug(f"Break for {v.name} at t = {time}.")
                case ShiftPlanEvent(time=time):
                    logger.info(f"Generating shift plan at t = {time}.")
                    for route in strategy.plan(self, event):
                        id_route = store(route)
                        assert id_route is not None

                        for event in self._plan_route(route, id_route):
                            events.push(event)
                case _:
                    msg = f"Unhandled event of type {type(event)}."
                    logger.error(msg)
                    raise ValueError(msg)

    def _plan_route(self, route: Route, id_route: int) -> Iterator[Event]:
        now = route.start_time
        break_idx = 0
        prev = 0  # start from depot

        for container_idx in route.plan:
            idx = container_idx + 1  # + 1 because 0 is depot

            if break_idx < len(self.config.BREAKS):
                _, late, break_dur = self.config.BREAKS[break_idx]

                # If servicing the current container makes us late for the
                # break, we first plan the break. A break is had at the depot.
                dep_travel = self.durations[prev, 0].item()
                cont_travel = self.durations[prev, idx].item()
                finish_at = now + cont_travel + self.config.TIME_PER_CONTAINER

                if (finish_at + dep_travel).time() > late:
                    # We're travelling back to the depot to take this break.
                    # Increases the break index, and yield a break event.
                    now += dep_travel
                    break_idx += 1

                    yield BreakEvent(now, id_route, break_dur, route.vehicle)

                    now += break_dur
                    prev = 0

            # Add travel duration from prev to current container, and start
            # service at the current container.
            now += self.durations[prev, idx].item()
            yield ServiceEvent(
                now,
                self.config.TIME_PER_CONTAINER,
                id_route=id_route,
                container=self.containers[container_idx],
                vehicle=route.vehicle,
            )

            now += self.config.TIME_PER_CONTAINER
            prev = idx
