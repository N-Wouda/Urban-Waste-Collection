from numpy.random import Generator, default_rng


class RandomStream:
    """
    Simple random stream generator. Must be seeded with an initial seed, and
    can then be queried for new random number streams.
    """

    def __init__(self, seed: int):
        self._seed = seed
        self._streams: dict[str, Generator] = {}

    def __call__(self, name: str) -> Generator:
        """
        Creates and returns a random number stream for the given name. If a
        stream already exists for the name, that stream is returned instead.
        """
        if name not in self._streams:
            self._streams[name] = default_rng(self._seed)

        return self._streams[name]
