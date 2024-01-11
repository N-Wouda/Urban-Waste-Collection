import numpy as np

from waste.classes import Simulator

from .GreedyStrategy import GreedyStrategy


class BaselineStrategy(GreedyStrategy):
    """
    A fairly faithful implementation of what the municipality is currently
    doing.

    Parameters
    ----------
    sim
        The simulation environment.
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
        sim: Simulator,
        deposit_volume: float,
        num_containers: int,
        max_runtime: float,
        **kwargs
    ):
        super().__init__(sim, num_containers, max_runtime, **kwargs)

        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        self.deposit_volume = deposit_volume

    def _get_container_idcs(self) -> np.ndarray[int]:
        containers = self.sim.containers

        if self.num_containers >= len(containers):
            return np.arange(0, len(containers))

        # Step 1. Determine current volume in each container based on the
        # current number of arrivals.
        arrivals = np.array([c.num_arrivals for c in containers])
        curr_vols = self.deposit_volume * arrivals

        # Step 2. Determine the amount of time it'll take for each container to
        # fill up, given the current volume and the average arrival rate.
        capacities = np.array([c.corrected_capacity for c in containers])
        max_extra = np.maximum(capacities - curr_vols, 0) / self.deposit_volume
        avg_rates = np.array([np.mean(c.rates) for c in containers])

        # Divide max_extra / avg_rates, with some special precautions in case
        # avg_rates is zero somewhere (we set num_hours to +inf in that case).
        num_hours = np.full_like(arrivals, fill_value=np.inf, dtype=float)
        num_hours = np.divide(
            max_extra,
            avg_rates,
            out=num_hours,
            where=~np.isclose(avg_rates, 0),
        )

        # Step 3. Select the ``num_containers`` that will fill up the soonest.
        top_k = np.argpartition(num_hours, self.num_containers)
        return top_k[: self.num_containers]
