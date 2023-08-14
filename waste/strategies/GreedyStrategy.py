import logging

import numpy as np
from pyvrp import Model
from pyvrp.stop import MaxRuntime

from waste.classes import Route, ShiftPlanEvent, Simulator
from waste.constants import DEPOT, TIME_PER_CONTAINER
from waste.functions import f2i

logger = logging.getLogger(__name__)


class GreedyStrategy:
    """
    A simple, greedy strategy that visits the containers with the largest
    number of arrivals since the last visit time.
    """

    def __init__(
        self, containers_per_route: int, max_runtime: float, **kwargs
    ):
        if containers_per_route < 0:
            raise ValueError("Expected containers_per_route >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.containers_per_route = containers_per_route
        self.max_runtime = max_runtime

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # Sort by arrivals, descending (highest number of arrivals first).
        sorted = np.argsort([-c.num_arrivals for c in sim.containers])
        c_idcs = sorted[: len(sim.vehicles) * self.containers_per_route]
        containers = [sim.containers[idx] for idx in c_idcs]

        m = Model()
        depot = m.add_depot(x=f2i(DEPOT[2]), y=f2i(DEPOT[3]))
        clients = [
            m.add_client(
                x=f2i(container.location[0]),
                y=f2i(container.location[1]),
                service_duration=TIME_PER_CONTAINER,
            )
            for container in containers
        ]

        for vehicle in sim.vehicles:
            m.add_vehicle_type(vehicle.capacity, num_available=1)

        dist = sim.distances
        dur = sim.durations

        for t_idx, this in enumerate(clients, 1):
            m.add_edge(this, depot, dist[t_idx, 0], dur[t_idx, 0])
            m.add_edge(depot, this, dist[0, t_idx], dur[0, t_idx])

            for o_idx, other in enumerate(clients[t_idx + 1 :], 1):
                m.add_edge(this, other, dist[t_idx, o_idx], dur[t_idx, o_idx])
                m.add_edge(other, this, dist[o_idx, t_idx], dur[o_idx, t_idx])

        res = m.solve(stop=MaxRuntime(self.max_runtime))

        if not res.is_feasible():
            msg = f"Shiftplan at time {event.time:.2f} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        return [
            Route(route.visits(), sim.vehicles[route.vehicle_type()])
            for route in res.best.get_routes()
        ]
