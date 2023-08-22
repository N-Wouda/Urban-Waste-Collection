import logging
from datetime import timedelta

import numpy as np
from pyvrp.stop import MaxRuntime

from waste.classes import (
    Event,
    LogisticRegression,
    Route,
    ServiceEvent,
    ShiftPlanEvent,
    Simulator,
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
    threshold
        From what overflow probability must a container be visited? This can
        be helpful in making sure containers with e.g. a 95% chance of being
        full are visited.
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
        threshold: float,
        deposit_volume: float,
        max_runtime: float,
        **kwargs,
    ):
        if rho < 0:
            raise ValueError("Expected rho >= 0.")

        if not (0 <= threshold <= 1):
            raise ValueError("Expected threshold in [0, 1].")

        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.rho = rho
        self.threshold = threshold
        self.max_runtime = max_runtime

        self.models: dict[int, LogisticRegression] = {
            id(container): LogisticRegression(container, deposit_volume)
            for container in sim.containers
        }

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        probs = [
            self.models[id(container)].prob(container.num_arrivals)
            for container in self.sim.containers
        ]

        model = make_model(
            self.sim,
            np.arange(len(self.sim.containers)),
            prizes=[int(self.rho * prob) for prob in probs],
            required=[prob > self.threshold for prob in probs],
        )

        result = model.solve(stop=MaxRuntime(self.max_runtime))
        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        return [
            Route(
                # PyVRP considers 0 the depot, and starts counting client
                # (container) indices from 1. So we need to subtract 1 from
                # the index returned by PyVRP.
                plan=[idx - 1 for idx in route],
                vehicle=self.sim.vehicles[route.vehicle_type()],
                start_time=event.time + timedelta(seconds=route.start_time()),
            )
            for route in result.best.get_routes()
        ]

    def observe(self, event: Event):
        if isinstance(event, ServiceEvent):
            container = event.container
            num_arrivals = event.num_arrivals
            has_overflow = event.volume > container.capacity

            model = self.models[id(container)]
            model.observe(num_arrivals, has_overflow)
