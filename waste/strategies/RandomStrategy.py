from numpy.random import Generator

from waste.classes import Event, Simulator


class RandomStrategy:
    """
    Random routing and dispatch strategy.
    """

    def __init__(self, gen: Generator):
        self.gen = gen

    def __call__(self, sim: Simulator, event: Event) -> list[Event]:
        # TODO
        return []
