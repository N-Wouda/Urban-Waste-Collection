import numpy as np

from waste.classes import Route, ShiftPlanEvent, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # TODO get parameter into the class somehow
        containers_per_route = 20

        with_arrivals = [c.num_arrivals > 0 for c in sim.containers]
        containers = sim.generator.choice(
            np.arange(len(sim.containers)),
            size=(len(sim.vehicles), containers_per_route),
            replace=False,
            p=with_arrivals / np.sum(with_arrivals),
        )

        return [
            Route(plan=list(plan), vehicle=vehicle)
            for plan, vehicle in zip(containers, sim.vehicles)
        ]
