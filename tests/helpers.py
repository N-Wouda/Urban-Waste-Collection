from __future__ import annotations

from typing import TYPE_CHECKING

from waste.classes import Route

if TYPE_CHECKING:
    from waste.classes import ShiftPlanEvent, Simulator


class NullStrategy:
    """
    Strategy that does nothing.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        return []


class PeriodicStrategy:
    """
    Strategy that generates routes in a deterministic, periodic, way. Vehicle i
    serves containers i, i+l, i+2l, ... where l is the number of vehicles.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        routes = []
        for i, vehicle in enumerate(sim.vehicles):
            plan = list(range(i, len(sim.containers), len(sim.vehicles)))
            routes.append(Route(plan, vehicle))
        return routes
