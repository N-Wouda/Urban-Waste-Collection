import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import pairwise

import numpy as np
from pyvrp.stop import MaxRuntime

from waste.classes import (
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


class PrizeCollectingStrategy:
    """
    Dispatching via prize-collecting by estimating overflow probabilities.

    Parameters
    ----------
    sim
        The simulation environment.
    rho
        Parameter that scales the overflow probability into a prize. This
        multiplier balances the goal of minimising distance on the one hand
        with the desire not to have overflows: small values prioritise limiting
        driving distance, while large values prioritise limiting overflows.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    definitely_full_after
        Upper bound on the number of deposits that fill up the largest
        container in the simulation.
    """

    def __init__(
        self,
        sim: Simulator,
        rho: float,
        deposit_volume: float,
        max_runtime: float,
        **kwargs,
    ):
        if rho < 0:
            raise ValueError("Expected rho >= 0.")

        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.rho = rho
        self.deposit_volume = deposit_volume
        self.max_runtime = max_runtime

        self.models: dict[int, OverflowModel] = {
            id(container): OverflowModel(container, deposit_volume)
            for container in sim.containers
        }

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # We use the vehicle's shift durations to model the breaks. Each break
        # starts and ends at a particular time. The shifts last from the start
        # of the shift plan to the beginning of the first break, and then from
        # the end of the first break to the beginning of the second, etc. until
        # the last shift, which lasts from the end of the last break to the end
        # of the shift plan duration.
        event_date = event.time.date()
        shifts: list[tuple[time, time]] = [
            (start, (datetime.combine(event_date, start) + dur).time())
            for start, dur in self.sim.config.BREAKS
        ]

        # Shift duration excludes breaks. We schedule those breaks as part of
        # the VRP we solve, so we need to add the time to the overall shift
        # duration to compensate.
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

        probs = [
            # Estimate the overflow probability *before* the next shift plan
            # moment (that is, before the next time we'll get to do something
            # about it). This is based on the number of arrivals that have
            # already happened (certainty) plus the rate of arrivals that'll
            # happen over the next 24 hours.
            self.models[id(c)].prob(c.num_arrivals, sum(c.rates))
            for c in self.sim.containers
        ]

        prizes = [int(self.rho * prob) for prob in probs]
        required = [
            # Rule of thumb: when the number of arrivals (each of the
            # assumed deposit volume) exceeds the capacity we definitely
            # have to visit the container.
            self.deposit_volume * c.num_arrivals > c.capacity
            for c in self.sim.containers
        ]

        logger.info(f"Planning {np.count_nonzero(required)} required visits.")
        logger.info(f"Average prize: {np.mean(prizes):.1f}m.")

        model = make_model(  # type: ignore
            self.sim,
            event,
            container_idcs=np.arange(len(self.sim.containers)),
            prizes=prizes,
            required=required,
            vehicles=vehicles,
            shift_duration=shift_duration,
        )

        result = model.solve(stop=MaxRuntime(self.max_runtime))
        logger.info(f"Visiting {result.best.num_clients()} containers.")

        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        # We split the vehicles around breaks in the above code, using multiple
        # shifts. We kept the vehicle names the same, and will now use that
        # together with the route start times to piece the different vehicle
        # routes back together.
        name2routes = defaultdict(list)
        name2vehicle = {veh.name: veh for veh in self.sim.vehicles}
        for route in result.best.get_routes():
            vehicle = vehicles[route.vehicle_type()]
            name2routes[vehicle.name].append(route)

        for name in name2routes:
            name2routes[name].sort(key=lambda route: route.start_time())

        return [
            Route(
                # PyVRP considers 0 the depot, and starts counting client
                # (container) indices from 1. So we need to subtract 1 from
                # the index returned by PyVRP.
                [idx - 1 for route in routes for idx in route],
                name2vehicle[name],
                event.time + timedelta(seconds=routes[0].start_time()),
            )
            for name, routes in name2routes.items()
        ]

    def observe(self, event: Event):
        if isinstance(event, ServiceEvent):
            container = event.container
            num_arrivals = event.num_arrivals
            has_overflow = event.volume > container.capacity

            model = self.models[id(container)]
            model.observe(num_arrivals, has_overflow)
