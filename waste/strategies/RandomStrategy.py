from typing import Iterator

import numpy as np
from numpy.random import Generator

from waste.classes import Route, Simulator
from waste.classes import ShiftPlanEvent as ShiftPlan


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: ShiftPlan) -> Iterator[Route]:
        # TODO get parameters into the class somehow
        NUM = 20

        p = np.array([c.num_arrivals for c in sim.containers], dtype=float)
        p /= p.sum()

        containers = self.gen.choice(
            np.arange(len(sim.containers)),
            size=(len(sim.vehicles), NUM),
            replace=False,
            p=p,
        )

        for idx, vehicle in enumerate(sim.vehicles):
            yield Route(plan=list(containers[idx]), vehicle=vehicle)
