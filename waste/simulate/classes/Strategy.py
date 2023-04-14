from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .Event import Event
    from .Simulator import Simulator


class Strategy(Protocol):
    """
    Protocol class that a simulation strategy should implement.
    """

    def __call__(self, sim: Simulator, event: Event) -> list[Event]:
        """
        Called for each SHIFT_PLAN event. This should handle the event, and
        return new events based on handling.
        """
        pass
