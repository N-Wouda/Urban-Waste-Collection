import numpy as np

from waste.classes import Simulator

from .GreedyStrategy import GreedyStrategy


class BaselineStrategy(GreedyStrategy):
    """
    A fairly faithful implementation of what the municipality is currently
    doing.

    Parameters
    ----------
    deposit_volume
        Assumed volume of the deposit with each arrival. This allows us to
        translate the number of arrivals into a total volume, and thus
        determine (as a rule-of-thumb) when a container will be full.
    num_containers
        See greedy.
    max_runtime
        See greedy.
    """

    def __init__(
        self,
        deposit_volume: float,
        num_containers: int,
        max_runtime: float,
        **kwargs
    ):
        super().__init__(num_containers, max_runtime, **kwargs)

        if deposit_volume < 0.0:
            raise ValueError("Expected deposit_volume >= 0.")

        self.deposit_volume = deposit_volume

    def _get_container_idcs(self, sim: Simulator) -> np.ndarray[int]:
        # TODO
        return np.array([])
