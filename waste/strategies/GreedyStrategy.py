import numpy as np
from numpy.random import Generator
from pyvrp import Client, ProblemData
from pyvrp.stop import MaxRuntime

from waste.classes import Route, ShiftPlanEvent, Simulator
from waste.constants import ID_DEPOT, SERVICE_TIME_PER_CONTAINER
from waste.functions import solve_vrp


class GreedyStrategy:
    """
    A simple, greedy strategy that visits the containers with the largest
    number of arrivals since the last visit time.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        end_of_shift = 4 * 3600  # in seconds

        num_vehicles = len(sim.vehicles)
        num_containers = 40 * num_vehicles

        arrivals = np.array([c.num_arrivals for c in sim.containers])
        selected = np.argsort(-arrivals)[:num_containers]
        ids = [ID_DEPOT] + list(selected + 1)
        indices = np.ix_(ids, ids)

        # Prepare the problem data instance for PyVRP, based on the selected
        # containers.
        containers = [
            Client(0, 0, 1, SERVICE_TIME_PER_CONTAINER, tw_late=end_of_shift)
            for _ in range(num_containers)
        ]
        dist = sim.distances[indices]
        dur = sim.durations[indices]
        clients = [Client(0, 0, tw_late=end_of_shift)] + containers
        data = ProblemData(clients, num_vehicles, 50, dist, dur)

        # Iterate and return the decisions as route objects.
        result = solve_vrp(data, MaxRuntime(10), seed=self.gen.integers(100))
        routes = result.best.get_routes()

        if not result.best.is_feasible():
            raise ValueError(f"Infeasible plan at t = {event.time}.")

        # Obtain route plans from PyVRP's solution and return those.
        plans = [[selected[stop - 1] for stop in route] for route in routes]
        return [
            Route(plan, sim.vehicles[idx]) for idx, plan in enumerate(plans)
        ]
