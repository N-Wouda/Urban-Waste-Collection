import logging
from datetime import timedelta

import numpy as np
from pyvrp.stop import MaxRuntime

from waste.classes import Event, Route, ShiftPlanEvent, Simulator
from waste.functions import make_model

logger = logging.getLogger(__name__)


class GreedyStrategy:
    """
    A simple, greedy strategy that visits the containers with the largest
    number of arrivals over capacity since the last visit time.

    Parameters
    ----------
    sim
        The simulation environment.
    num_containers
        Number of containers to schedule.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    """

    def __init__(
        self, sim: Simulator, num_containers: int, max_runtime: float, **kwargs
    ):
        if num_containers < 0:
            raise ValueError("Expected num_containers >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.num_containers = num_containers
        self.max_runtime = max_runtime

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        container_idcs = self._get_container_idcs()
        model = make_model(self.sim, event, container_idcs)

        result = model.solve(stop=MaxRuntime(self.max_runtime))
        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        return [
            Route(
                # PyVRP considers 0 the depot, and starts counting client
                # (container) indices from 1. So we need to subtract 1 from
                # the index returned by PyVRP before we map back to the
                # container indices.
                plan=[container_idcs[idx - 1] for idx in route],
                vehicle=self.sim.vehicles[route.vehicle_type()],
                start_time=event.time + timedelta(seconds=route.start_time()),
            )
            for route in result.best.get_routes()
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy

    def _get_container_idcs(self) -> np.ndarray[int]:
        if self.num_containers >= len(self.sim.containers):
            return np.arange(0, len(self.sim.containers))

        # Returns indices of the containers with the highest number of arrivals
        # over container size. This measure is a proxy for the container fill
        # rate at shift plan time.
        measure = [c.num_arrivals / c.capacity for c in self.sim.containers]
        top_k = np.argpartition(measure, -self.num_containers)
        return top_k[-self.num_containers :]
