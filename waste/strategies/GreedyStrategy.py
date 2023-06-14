import numpy as np
from numpy.random import Generator
from pyvrp import Client, ProblemData
from pyvrp.stop import MaxRuntime

from waste.classes import Route, ShiftPlanEvent, Simulator
from waste.constants import BREAKS, DEPOT, ID_DEPOT, TIME_PER_CONTAINER
from waste.functions import solve_vrp


class GreedyStrategy:
    """
    A simple, greedy strategy that visits the containers with the largest
    number of arrivals since the last visit time.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        shift_duration = int(8.5 * 3600)  # in seconds
        num_vehicles = len(sim.vehicles)  # number of available vehicles
        num_containers = 50 * num_vehicles  # number of containers to empty

        arrivals = np.array([c.num_arrivals for c in sim.containers])
        selected = np.argsort(-arrivals)[:num_containers]
        ids = [ID_DEPOT] + list(selected + 1)
        indices = np.ix_(ids, ids)

        # Prepare the problem data instance for PyVRP, based on the selected
        # containers.
        clients = []
        for idx in range(num_containers):
            container = sim.containers[selected[idx]]
            location = container.location
            loc = _loc2int(location[1]), _loc2int(location[0])
            serv_time = TIME_PER_CONTAINER
            clients.append(Client(*loc, 0, serv_time, tw_late=shift_duration))

        depot_loc = _loc2int(DEPOT[3]), _loc2int(DEPOT[2])
        depot = Client(depot_loc, tw_late=shift_duration)

        # Coffee and lunch breaks, one of each for each vehicle. These are at
        # the depot, and the time windows are such that one of each must be
        # placed in each route.
        breaks = [
            Client(
                *depot_loc,
                0,
                break_time,
                int(start * 3_600),
                int(end * 3_600),
            )
            for break_time, start, end in BREAKS
            for _ in range(num_vehicles)
        ]

        stops = [depot] + clients + breaks

        dist = np.empty((len(stops), len(stops)), dtype=int)
        dist[: len(ids), : len(ids)] = sim.distances[indices]
        dist[len(ids) :, len(ids) :] = 0
        dist[len(ids) :, : len(ids)] = dist[0, : len(ids)]
        dist[: len(ids), len(ids) :] = np.atleast_2d(dist[: len(ids), 0]).T

        dur = np.empty((len(stops), len(stops)), dtype=int)
        dur[: len(ids), : len(ids)] = sim.durations[indices]
        dur[len(ids) :, len(ids) :] = 0
        dur[len(ids) :, : len(ids)] = dur[0, : len(ids)]
        dur[: len(ids), len(ids) :] = np.atleast_2d(dur[: len(ids), 0]).T

        data = ProblemData(stops, num_vehicles, 0, dist, dur)

        # Iterate and return the decisions as route objects.
        result = solve_vrp(data, MaxRuntime(10), seed=self.gen.integers(100))
        routes = result.best.get_routes()

        if not result.best.is_feasible():
            raise ValueError(f"Infeasible plan at t = {event.time}.")

        # Obtain route plans from PyVRP's solution and return those. Ignore
        # routes that do not have any 'real' stops: those are empty (but do
        # still visit the imaginary coffee and lunch break stops).
        plans = [
            [selected[stop - 1] for stop in route if stop <= len(selected)]
            for route in routes
        ]

        return [
            Route(plan, sim.vehicles[idx])
            for idx, plan in enumerate(plans)
            if len(plan) != 0
        ]


def _loc2int(loc: float) -> int:
    return int(10_000 * loc)
