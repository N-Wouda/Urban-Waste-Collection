import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import pairwise

from pyvrp.stop import MaxRuntime

from waste.classes import (
    ArrivalEvent,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.functions import make_model

logger = logging.getLogger(__name__)


class LookAheadStrategy:
    """
    This strategy uses a lookahead horizon on all container deposit events to
    plan exactly the containers that need to emptied before the end of the
    horizon, and nothing more.

    Parameters
    ----------
    sim
        The simulation environment.
    horizon
        Lookahead horizon.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    """

    def __init__(
        self,
        sim: Simulator,
        horizon: timedelta,
        max_runtime: float,
        **kwargs,
    ):
        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        if horizon.total_seconds() < 0:
            raise ValueError("Expected horizon >= 0 hours.")

        self.sim = sim
        self.horizon = horizon
        self.max_runtime = max_runtime

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # We use the same vehicle planning procedure as in the prize collection
        # strategy. See the comments there.
        event_date = event.time.date()
        shifts: list[tuple[time, time]] = [
            (start, (datetime.combine(event_date, start) + dur).time())
            for start, dur in self.sim.config.BREAKS
        ]

        event_time = event.time.time()
        shift_duration = sum(
            (dur for _, dur in self.sim.config.BREAKS),
            start=self.sim.config.SHIFT_DURATION,
        )

        shifts.insert(0, (time.min, event_time))
        shifts.append(((event.time + shift_duration).time(), time.max))

        vehicles = [
            Vehicle(vehicle.name, vehicle.capacity, start, end)
            for vehicle in self.sim.vehicles
            for (_, start), (end, _) in pairwise(shifts)
        ]

        cluster_idcs = self._get_cluster_idcs(now=event.time)
        model = make_model(  # type: ignore
            self.sim,
            event,
            cluster_idcs=cluster_idcs,
            vehicles=vehicles,
            shift_duration=shift_duration,
        )

        result = model.solve(
            stop=MaxRuntime(self.max_runtime),
            seed=self.sim.generator.integers(100),
        )

        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        name2routes = defaultdict(list)
        name2vehicle = {veh.name: veh for veh in self.sim.vehicles}
        for route in result.best.get_routes():
            vehicle = vehicles[route.vehicle_type()]
            name2routes[vehicle.name].append(route)

        for name in name2routes:
            name2routes[name].sort(key=lambda route: route.start_time())

        return [
            Route(
                [idx - 1 for route in routes for idx in route],
                name2vehicle[name],
                event.time + timedelta(seconds=routes[0].start_time()),
            )
            for name, routes in name2routes.items()
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy

    def _get_cluster_idcs(self, now: datetime) -> list[int]:
        latest = now + self.horizon
        clusters = self.sim.clusters
        cluster2idx = {c: i for i, c in enumerate(clusters)}

        # Look ahead strategies use perfect information about the current and
        # future fill levels of containers.
        volumes = [c.volume for c in clusters]
        for event in self.sim.events:
            if now <= event.time <= latest and isinstance(event, ArrivalEvent):
                volumes[cluster2idx[event.cluster]] += event.volume

        # We need to empty all container clusters whose volume will exceed
        # capacity by the end of the lookahead horizon.
        return [
            idx
            for idx, cluster in enumerate(clusters)
            if volumes[idx] >= cluster.capacity
        ]
