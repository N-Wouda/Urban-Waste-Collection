from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from waste.classes import Route, ShiftPlanEvent, Simulator


class NullStrategy:
    """
    Strategy that does nothing.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        return []


class MockStrategy:
    """
    Simple mock strategy that returns the same routes upon each call.
    """

    def __init__(self, routes: list[Route], **kwargs):
        self.routes = routes

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        return self.routes


def dist(mat: np.ndarray, routes: list[Route]) -> int:
    dist = 0
    for route in routes:
        plan = np.array(route.plan)
        stops = [0, *(plan + 1), 0]
        for idx, stop in enumerate(route.plan[1:], 1):
            dist += mat[stops[idx - 1], stop]
    return dist
