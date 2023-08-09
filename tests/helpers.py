from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from waste.classes import Route, ShiftPlanEvent, Simulator


class NullStrategy:
    """
    Strategy that does nothing.
    """

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        return []
