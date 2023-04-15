from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .baseline import baseline
from .prize import prize
from .random import random

if TYPE_CHECKING:
    from waste.classes.Event import Event
    from waste.classes.Simulator import Simulator

    Strategy = Callable[[Simulator, Event], list[Event]]

STRATEGIES: dict[str, Strategy] = {
    "baseline": baseline,
    "prize": prize,
    "random": random,
}
