from .classes import Container, Environment, Event, Strategy, Vehicle
from .random import random

STRATEGIES: dict[str, Strategy] = {
    "random": random,
}
