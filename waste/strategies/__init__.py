from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .random import random

if TYPE_CHECKING:
    from waste.classes.Event import Event
    from waste.classes.Simulator import Simulator

    Strategy = Callable[[Simulator, Event], list[Event]]

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
