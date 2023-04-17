from typing import Iterator

import numpy as np
from numpy.random import Generator

from waste.classes import Route
from waste.classes import ShiftPlanEvent as ShiftPlan
from waste.classes import Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: ShiftPlan) -> Iterator[Route]:
        NUM = 40

        p = np.array([c.num_arrivals for c in sim.containers], dtype=float)
        p /= p.sum()

        containers = self.gen.choice(
            sim.containers,
            size=(len(sim.vehicles), NUM),
            replace=False,
            p=p,
        )

        for idx, vehicle in enumerate(sim.vehicles):
            times = sorted(np.random.uniform(event.time, event.time + 6, NUM))
            yield Route(
                plan=[(t, c) for t, c in zip(times, containers[idx])],
                vehicle=vehicle,
            )
