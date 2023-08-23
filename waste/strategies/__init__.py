from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .BaselineStrategy import BaselineStrategy as BaselineStrategy
from .GreedyStrategy import GreedyStrategy as GreedyStrategy
from .PrizeCollectingStrategy import (
    PrizeCollectingStrategy as PrizeCollectingStrategy,
)
from .RandomStrategy import RandomStrategy as RandomStrategy

if TYPE_CHECKING:
    from waste.classes import Event, Route, ShiftPlanEvent, Simulator


class Strategy(Protocol):

    # Should be able to take arbitrary arguments, some of which may be
    # discarded. This makes it much easier to work with the strategies from
    # the simulate entrypoint.
    def __init__(self, sim: Simulator, **kwargs):
        pass

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        pass

    def observe(self, event: Event):
        pass


STRATEGIES: dict[str, type[Strategy]] = {
    "baseline": BaselineStrategy,  # type: ignore
    "greedy": GreedyStrategy,  # type: ignore
    "prize": PrizeCollectingStrategy,  # type: ignore
    "random": RandomStrategy,  # type: ignore
}
