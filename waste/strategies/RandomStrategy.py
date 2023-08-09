import numpy as np

from waste.classes import Route, ShiftPlanEvent, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # TODO get parameters into the class somehow
        NUM = 20

        p = np.array([c.num_arrivals for c in sim.containers], dtype=float)
        p /= p.sum()

        containers = sim.generator.choice(
            np.arange(len(sim.containers)),
            size=(len(sim.vehicles), NUM),
            replace=False,
            p=p,
        )

        return [
            Route(plan=list(containers[idx]), vehicle=vehicle)
            for idx, vehicle in enumerate(sim.vehicles)
        ]
