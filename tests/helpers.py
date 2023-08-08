from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from numpy.random import Generator

    from waste.classes.Event import ShiftPlanEvent as ShiftPlan
    from waste.classes.Route import Route
    from waste.classes.Simulator import Simulator


class NullStrategy:
    """
    Strategy that does nothing.
    """

    def __init__(self, gen: Generator = None):
        pass

    def __call__(self, sim: Simulator, event: ShiftPlan) -> list[Route]:
        return []