import logging
from collections import defaultdict
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
        self.rho = rho
        self.threshold = threshold
        self.max_runtime = max_runtime

        self.sim = sim
        self.data: dict[int, list[tuple[int, bool]]] = defaultdict(list)
        self.models: list[SGDClassifier] = []

        for _ in sim.containers:
            model = SGDClassifier(
                loss="log_loss",
                penalty=None,
                fit_intercept=False,
            )

            model.fit([0, 100], [0, 1])  # TODO make this data an argument
            self.models.append(model)

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # Step 1. Update the models with data observed since the last shift
        # plan, clear the data, and compute the overflow probabilities.
        for idx, container in enumerate(self.sim.containers):
            data = np.array(self.data[id(container)])
            self.models[idx].partial_fit(data[0, :], data[1, :])
            self.data[id(container)] = []

        probs = [
            m.predict_proba(c.num_arrivals)
            for c, m in zip(self.sim.containers, self.models)
        ]

        # Step 2. Determine prizes, required containers, and solve the VRP.
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

        # Step 3. Return the route plan.
        return [
            Route(
                # PyVRP considers 0 the depot, and start counting client
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
            # Store the new observations. We will update the model in one batch
            # the next time we plan a shift.
            container = event.container
            num_arrivals = event.num_arrivals
            has_overflow = event.volume > container.capacity
            obs = (num_arrivals, has_overflow)

            logger.debug(f"Adding observation for {container.name}: {obs}.")
            self.data[id(container)].append(obs)
