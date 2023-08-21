from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from waste.classes import Event, Route, ShiftPlanEvent, Simulator


class NullStrategy:
    """
    Strategy that does nothing.
    """

    def __init__(self, sim: Simulator, **kwargs):
        pass

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        return []

    def observe(self, event: Event):
        pass  # unused by this strategy


class MockStrategy:
    """
    Simple mock strategy that returns the same routes upon each call.
    """

    def __init__(self, sim: Simulator, routes: list[Route], **kwargs):
        self.routes = routes

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        return self.routes

    def observe(self, event: Event):
        pass  # unused by this strategy


def cum_value(mat: np.ndarray, routes: list[Route]):
    """
    Computes the total cumulative value of all routes in the route plan, given
    the matrix describing the edge values. This is a dead simple implementation
    so that we know for sure it's correct.
    """
    cum_val = np.array([0], dtype=mat.dtype)

    for route in routes:
        plan = np.array(route.plan)
        stops = [0, *(plan + 1), 0]
        for idx, stop in enumerate(stops[1:], 1):
            cum_val += mat[stops[idx - 1], stop]

    return cum_val.item()
