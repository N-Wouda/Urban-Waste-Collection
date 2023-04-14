from .classes import (
    Container,
    Database,
    Event,
    EventType,
    RandomStream,
    Simulator,
    Strategy,
    Vehicle,
)
from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
