# isort: off

from .classes import (
    Container,
    Environment,
    Event,
    RandomStream,
    Strategy,
    Vehicle,
)

# isort: on

from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
