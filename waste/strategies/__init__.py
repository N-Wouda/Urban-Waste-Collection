from waste.classes import Strategy

from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
