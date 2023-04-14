from itertools import count

from numpy.random import Generator, default_rng


class RandomStream:
    """
    Simple random stream generator. Must be seeded with an initial seed, and
    can then be queried for new random number streams that each have a fixed
    seed.
    """

    def __init__(self, seed: int):
        self._seeder = count(seed)

    def get_stream(self) -> Generator:
        return default_rng(next(self._seeder))
