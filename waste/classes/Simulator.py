from __future__ import annotations

import logging
from datetime import datetime
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

    from .Cluster import Cluster
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
        clusters: list[Cluster],
        vehicles: list[Vehicle],
        config: Configuration = Configuration(),
    ):
        self.generator = generator
        self.depot = depot
        self.distances = distances
        self.durations = durations
        self.clusters = clusters
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
        events.

        Parameters
        ----------
        store
            Function that is called for each new event. Can be used to log
            events to e.g. a database.
        strategy
            Shift plan strategy to apply. Is called to generate new shift
            plans on shift plan events.
        initial_events
            Initial list of events to seed the simulation with.
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
                case ArrivalEvent(time=time, cluster=c, volume=vol):
                    logger.debug(f"Arrival at {c.name} at t = {time}.")
                    c.arrive(vol)
                case ServiceEvent(time=time, cluster=c):
                    logger.debug(f"Service at {c.name} at t = {time}.")
                    c.service()
                case BreakEvent(time=time, vehicle=v):
                    logger.debug(f"Break for {v.name} at t = {time}.")
                case ShiftPlanEvent(time=time):
                    logger.info(f"Generating shift plan at t = {time}.")
                    for route in strategy.plan(event):
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
        prev = 0  # start from depot

        # We filter the breaks: only those breaks that are *after* the route's
        # start time must be taken. If we start later than a break, we can
        # freely skip that one.
        break_idx = 0
        breaks = [
            (start, break_dur)
            for start, break_dur in self.config.BREAKS
            if datetime.combine(now.date(), start) >= route.start_time
        ]

        for cluster_idx in route.plan:
            idx = cluster_idx + 1  # + 1 because 0 is depot
            cluster = self.clusters[cluster_idx]

            service_duration = (
                self.config.TIME_PER_CLUSTER
                + cluster.num_containers * self.config.TIME_PER_CONTAINER
            )

            if break_idx < len(breaks):
                start, break_dur = breaks[break_idx]
                break_start = datetime.combine(now.date(), start)

                # If servicing the current cluster makes us late for the break,
                # we first plan the break. A break is had at the depot.
                travel = self.durations[prev, idx].item()
                finish_at = now + travel + service_duration

                if finish_at + self.durations[idx, 0].item() > break_start:
                    # We're travelling back to the depot to take this break.
                    # Increases the break index, and yield a break event.
                    break_idx += 1

                    # We travel back to the depot, which takes less time than
                    # the start of the break. So we have to wait a little bit,
                    # and then have the break starting at the start_time.
                    assert break_start >= now + self.durations[prev, 0].item()
                    now = break_start

                    yield BreakEvent(now, break_dur, id_route, route.vehicle)

                    now += break_dur
                    prev = 0

            # Travel from prev to current cluster, and start service there.
            now += self.durations[prev, idx].item()

            yield ServiceEvent(
                now,
                service_duration,
                id_route=id_route,
                cluster=cluster,
                vehicle=route.vehicle,
            )

            now += service_duration
            prev = idx
