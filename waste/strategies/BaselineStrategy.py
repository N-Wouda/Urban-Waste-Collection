from numpy.random import Generator

from waste.classes import Event, Simulator


class BaselineStrategy:
    """
    A fairly faithful implementation of what the municipality is currently
    doing.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: Event) -> list[Event]:
        # TODO
        return []
