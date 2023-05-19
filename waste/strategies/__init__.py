from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol

from .BaselineStrategy import BaselineStrategy
from .GreedyStrategy import GreedyStrategy
from .PrizeCollectingStrategy import PrizeCollectingStrategy

if TYPE_CHECKING:
    from numpy.random import Generator

    from waste.classes.Event import ShiftPlanEvent as ShiftPlan
    from waste.classes.Route import Route
    from waste.classes.Simulator import Simulator


class Strategy(Protocol):
    def __init__(self, gen: Generator):
        pass

    def __call__(self, sim: Simulator, event: ShiftPlan) -> Iterator[Route]:
        pass


STRATEGIES: dict[str, Strategy] = {
    "baseline": BaselineStrategy,
    "prize": PrizeCollectingStrategy,
    "greedy": GreedyStrategy,
}
