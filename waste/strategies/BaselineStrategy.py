import numpy as np

from waste.classes import Simulator

from .GreedyStrategy import GreedyStrategy


class BaselineStrategy(GreedyStrategy):
    """
    A fairly faithful implementation of what the municipality is currently
    doing.

    Parameters
    ----------
    unit_threshold
        Threshold value per unit of container capacity. If there are more
        arrivals than this threshold (scaled by the container capacity), then
        the container is assumed to be full. We use this to extrapolate when
        a container will be full.
    """

    def __init__(self, unit_threshold: float, **kwargs):
        super().__init__(**kwargs)

        if unit_threshold < 0.0:
            raise ValueError("Expected unit_threshold >= 0.")

        self.unit_threshold = unit_threshold

    def _get_container_idcs(self, sim: Simulator) -> np.ndarray[int]:
        # TODO
        return np.array([])
