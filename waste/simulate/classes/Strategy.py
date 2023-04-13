from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .Environment import Environment
    from .Event import Event


class Strategy(Protocol):
    """
    Protocol class that a simulation strategy should implement.
    """

    def __call__(self, env: Environment, event: Event) -> list[Event]:
        """
        Called for each event. This should handle the event, and return new
        events based on handling.
        """
        pass
