import numpy as np
from numpy.random import Generator

from waste.classes import Event, Route, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: Event) -> list[Route]:
        NUM = 40

        p = np.array([c.num_arrivals for c in sim.containers], dtype=float)
        p /= p.sum()

        containers = self.gen.choice(
            sim.containers, size=NUM * len(sim.vehicles), replace=False, p=p
        )

        routes = []

        for idx, vehicle in enumerate(sim.vehicles):
            times = np.linspace(event.time, event.time + 6, num=NUM)
            plan = containers[idx * NUM : (idx + 1) * NUM]
            routes.append(
                Route(
                    plan=[(t, c) for t, c in zip(times, plan)],
                    vehicle=vehicle,
                )
            )

        return routes
