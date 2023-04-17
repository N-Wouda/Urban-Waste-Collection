from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .BaselineStrategy import BaselineStrategy
from .PrizeCollectingStrategy import PrizeCollectingStrategy
from .RandomStrategy import RandomStrategy

if TYPE_CHECKING:
    from numpy.random import Generator

    from waste.classes.Event import Event
    from waste.classes.Route import Route
    from waste.classes.Simulator import Simulator


class Strategy(Protocol):
    def __init__(self, gen: Generator):
        pass

    def __call__(self, sim: Simulator, event: Event) -> list[Route]:
        pass


STRATEGIES: dict[str, Strategy] = {
    "baseline": BaselineStrategy,
    "prize": PrizeCollectingStrategy,
    "random": RandomStrategy,
}
