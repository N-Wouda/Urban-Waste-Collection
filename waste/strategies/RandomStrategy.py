import numpy as np

from waste.classes import Event, Route, ShiftPlanEvent, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, sim: Simulator, clusters_per_route: int, **kwargs):
        if clusters_per_route < 0:
            raise ValueError("Expected clusters_per_route >= 0.")

        self.sim = sim
        self.clusters_per_route = clusters_per_route

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # We select randomly from clusters with arrivals, favouring those
        # with more arrivals.
        arrivals = [c.num_arrivals for c in self.sim.clusters]
        clusters = self.sim.generator.choice(
            np.arange(len(self.sim.clusters)),
            size=(len(self.sim.vehicles), self.clusters_per_route),
            replace=False,
            p=arrivals / np.sum(arrivals),
        )

        return [
            Route(plan=list(plan), vehicle=vehicle, start_time=event.time)
            for plan, vehicle in zip(clusters, self.sim.vehicles)
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy
