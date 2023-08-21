import numpy as np

from waste.classes import Event, Route, ShiftPlanEvent, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, containers_per_route: int, **kwargs):
        if containers_per_route < 0:
            raise ValueError("Expected containers_per_route >= 0.")

        self.containers_per_route = containers_per_route

    def plan(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # We select randomly from containers with arrivals, favouring those
        # with more arrivals.
        arrivals = [c.num_arrivals for c in sim.containers]
        containers = sim.generator.choice(
            np.arange(len(sim.containers)),
            size=(len(sim.vehicles), self.containers_per_route),
            replace=False,
            p=arrivals / np.sum(arrivals),
        )

        return [
            Route(plan=list(plan), vehicle=vehicle, start_time=event.time)
            for plan, vehicle in zip(containers, sim.vehicles)
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy
