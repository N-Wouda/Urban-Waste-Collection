from .classes import (
    Container,
    Database,
    Event,
    EventType,
    Simulator,
    Strategy,
    Vehicle,
)
from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
