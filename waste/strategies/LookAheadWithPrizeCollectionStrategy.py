import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import pairwise

import numpy as np
from pyvrp.stop import MaxRuntime

from waste.classes import (
    ArrivalEvent,
    Event,
    OverflowModel,
    Route,
    ServiceEvent,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.functions import make_model

logger = logging.getLogger(__name__)


class LookAheadWithPrizeStrategy:
    """
    This strategy uses lookahead to set a weight between 0 and 1 to empty
    a container. This weight corresponds to the overflow probability in the
    prize collection strategy, but since lookahead is used, this weight should
    not be interpreted as a probability. The default container weight is 0.


    Parameters
    ----------
    sim
        The simulation environment.
    horizon1
        All containers that fill up before horizon1 receive weight 1
    horizon2
        All containers that fill up between horizon1 and horizon2 receive
        weight_thres
    horizon3
        All containers that fill up between horizon2 and horizon3 receive
        weight_thres.
    weight_thres2
        Weight for containers that fill up between horizon1 and horizon2.
    weight_thres3
        Weight for containers that fill up between horizon2 and horizon3.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    rho
        See the prize collection strategy
    max_runtime
        See the prize collection strategy
    perfect_information
        See the prize collection strategy
    """

    def __init__(
        self,
        sim: Simulator,
        horizon1: timedelta,
        horizon2: timedelta,
        horizon3: timedelta,
        weight_thres2: float,
        weight_thres3: float,
        rho: float,
        max_runtime: float,
        perfect_information: bool = False,
        **kwargs,
    ):
        if (
            min(
                horizon1.total_seconds(),
                horizon2.total_seconds(),
                horizon3.total_seconds(),
            )
            < 0
        ):
            raise ValueError("Expected horizons >= 0 hours.")

        if weight_thres2 < 0 or weight_thres3 < 0:
            raise ValueError("Expected weight thresholds >= 0")

        if rho < 0:
            raise ValueError("Expected rho >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.horizon1 = horizon1
        self.horizon2 = horizon2
        self.horizon3 = horizon3
        self.weight_thres2 = weight_thres2
        self.weight_thres3 = weight_thres3
        self.rho = rho
        self.max_runtime = max_runtime
        self.perfect_information = perfect_information

        self.models: dict[int, OverflowModel] = {
            id(cluster): OverflowModel(cluster) for cluster in sim.clusters
        }

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

        weights = self._get_weights(now=event.time)
        prizes = [int(self.rho * weight) for weight in weights]
        required = [np.isclose(weight, 1.0, rtol=1e-6) for weight in weights]

        logger.info(f"Planning {np.count_nonzero(required)} required visits.")
        logger.info(f"Average prize: {np.mean(prizes):.1f}m.")

        model = make_model(  # type: ignore
            self.sim,
            event,
            cluster_idcs=np.arange(len(self.sim.clusters)),
            prizes=prizes,
            required=required,
            vehicles=vehicles,
            shift_duration=shift_duration,
        )

        result = model.solve(
            stop=MaxRuntime(self.max_runtime),
            seed=self.sim.generator.integers(100),
        )

        msg = f"Visiting {result.best.num_clients()} container clusters."
        logger.info(msg)

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
        if isinstance(event, ServiceEvent):
            cluster = event.cluster
            num_arrivals = event.num_arrivals
            has_overflow = event.volume > cluster.capacity

            model = self.models[id(cluster)]
            model.observe(num_arrivals, has_overflow)

    def _get_weights(self, now: datetime) -> list[float]:
        latest = now + self.horizon3
        relevant_events = {
            event
            for event in self.sim.events
            if now <= event.time <= latest and isinstance(event, ArrivalEvent)
        }

        def compute_volumes(end: datetime) -> list[float]:
            volumes = [c.volume for c in clusters]
            for event in relevant_events:
                if event.time <= end:
                    volumes[cluster2idx[event.cluster]] += event.volume
            return volumes

        clusters = self.sim.clusters
        cluster2idx = {c: i for i, c in enumerate(clusters)}

        # default weight
        weights: list[float] = [0.0] * len(clusters)

        # Handle first the least critical containers
        volumes = compute_volumes(now + self.horizon3)
        for idx, cluster in enumerate(clusters):
            if volumes[idx] >= cluster.capacity:
                weights[idx] = self.weight_thres3

        # Now the medium critical containers
        volumes = compute_volumes(now + self.horizon2)
        for idx, cluster in enumerate(clusters):
            if volumes[idx] >= cluster.capacity:
                weights[idx] = self.weight_thres2

        # Update the required containers
        volumes = compute_volumes(now + self.horizon1)
        for idx, cluster in enumerate(clusters):
            if volumes[idx] >= cluster.capacity:
                weights[idx] = 1

        return weights
