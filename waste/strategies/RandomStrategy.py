import numpy as np

from waste.classes import Event, Route, ShiftPlanEvent, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, sim: Simulator, containers_per_route: int, **kwargs):
        if containers_per_route < 0:
            raise ValueError("Expected containers_per_route >= 0.")

        self.sim = sim
        self.containers_per_route = containers_per_route

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # We select randomly from containers with arrivals, favouring those
        # with more arrivals.
        arrivals = [c.num_arrivals for c in self.sim.containers]
        containers = self.sim.generator.choice(
            np.arange(len(self.sim.containers)),
            size=(len(self.sim.vehicles), self.containers_per_route),
            replace=False,
            p=arrivals / np.sum(arrivals),
        )

        return [
            Route(plan=list(plan), vehicle=vehicle, start_time=event.time)
            for plan, vehicle in zip(containers, self.sim.vehicles)
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy
