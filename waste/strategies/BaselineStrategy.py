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

        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        self.deposit_volume = deposit_volume

    def _get_container_idcs(self, sim: Simulator) -> np.ndarray[int]:
        # Step 1. Determine current volume in each container based on the
        # current number of arrivals.
        arrivals = np.array([c.num_arrivals for c in sim.containers])
        curr_vol = self.deposit_volume * arrivals

        # Step 2. Determine the amount of time it'll take for each container to
        # fill up, given the current volume and the average arrival rate.
        capacities = np.array([c.capacity for c in sim.containers])
        max_extra = np.maximum(capacities - curr_vol, 0) / self.deposit_volume
        avg_rates = np.array([np.mean(c.rates) for c in sim.containers])
        num_hours = max_extra / avg_rates

        # Step 3. Select the ``num_containers`` that will fill up the soonest.
        top_k = np.argpartition(num_hours, self.num_containers)
        return top_k[: self.num_containers]
