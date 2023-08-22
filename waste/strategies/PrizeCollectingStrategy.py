import logging
from datetime import timedelta

import numpy as np
from pyvrp.stop import MaxRuntime
from sklearn.linear_model import SGDClassifier

from waste.classes import Event, Route, ServiceEvent, ShiftPlanEvent, Simulator
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
    """

    def __init__(
        self,
        sim: Simulator,
        rho: float,
        threshold: float,
        max_runtime: float,
        **kwargs,
    ):
        self.sim = sim
        self.rho = rho
        self.threshold = threshold
        self.max_runtime = max_runtime

        self.models: dict[int, SGDClassifier] = {}
        for container in sim.containers:
            model = SGDClassifier(
                loss="log_loss",
                penalty=None,
                fit_intercept=False,
            )

            model.fit([0, 100], [0, 1])  # TODO make this data an argument
            self.models[id(container)] = model

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        probs = [
            self.models[id(c)].predict_proba(c.num_arrivals)
            for c in self.sim.containers
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
        if not isinstance(event, ServiceEvent):
            return

        container = event.container
        x = event.num_arrivals
        y = event.volume > container.capacity
        logger.debug(f"Observing ({x}, {y}) for {container.name}.")

        model = self.models[id(container)]
        model.partial_fit(x, y)
        logger.debug(f"Updated coefficient to {model.coef_:.2f}.")
