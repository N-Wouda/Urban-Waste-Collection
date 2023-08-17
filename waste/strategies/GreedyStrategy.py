import logging

import numpy as np
from pyvrp import Model
from pyvrp.stop import MaxRuntime

from waste.classes import Container, Route, ShiftPlanEvent, Simulator
from waste.constants import DEPOT, SHIFT_DURATION, TIME_PER_CONTAINER
from waste.functions import f2i

logger = logging.getLogger(__name__)


class GreedyStrategy:
    """
    A simple, greedy strategy that visits the containers with the largest
    number of arrivals since the last visit time.

    Parameters
    ----------
    num_containers
        Number of containers to schedule.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    """

    def __init__(self, num_containers: int, max_runtime: float, **kwargs):
        if num_containers < 0:
            raise ValueError("Expected num_containers >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.num_containers = num_containers
        self.max_runtime = max_runtime

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        container_idcs = self._get_container_idcs(sim)
        containers = [sim.containers[idx] for idx in container_idcs]
        model = self._make_model(sim, containers)
        result = model.solve(stop=MaxRuntime(self.max_runtime))

        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time:.2f} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        return [
            Route(
                # PyVRP considers 0 the depot. So we need to subtract one, and
                # then map that back to an index the simulator understands.
                plan=[container_idcs[idx - 1] for idx in route],
                vehicle=sim.vehicles[route.vehicle_type()],
            )
            for route in result.best.get_routes()
        ]

    def _make_model(
        self, sim: Simulator, containers: list[Container]
    ) -> Model:
        model = Model()
        model.add_depot(
            x=f2i(DEPOT[2]),
            y=f2i(DEPOT[3]),
            tw_late=int(SHIFT_DURATION.total_seconds()),
        )

        for container in containers:
            model.add_client(
                x=f2i(container.location[0]),
                y=f2i(container.location[1]),
                service_duration=int(TIME_PER_CONTAINER.total_seconds()),
                tw_late=int(SHIFT_DURATION.total_seconds()),
            )

        for vehicle in sim.vehicles:
            model.add_vehicle_type(
                capacity=int(vehicle.capacity), num_available=1
            )

        distances = sim.distances.astype(int)
        durations = sim.durations.astype(int)

        for frm_idx, frm in enumerate(model.locations):
            for to_idx, to in enumerate(model.locations):
                model.add_edge(
                    frm,
                    to,
                    distances[frm_idx, to_idx],
                    durations[frm_idx, to_idx],
                )

        return model

    def _get_container_idcs(self, sim: Simulator) -> list[int]:
        # Sort by arrivals, descending (highest number of arrivals first).
        sorted = np.argsort([-c.num_arrivals for c in sim.containers])
        return sorted[: self.num_containers]
