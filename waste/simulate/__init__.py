from .classes import (
    Container,
    Environment,
    Event,
    EventType,
    RandomStream,
    Strategy,
    Vehicle,
)
from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
