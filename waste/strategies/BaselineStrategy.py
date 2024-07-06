import logging
from datetime import timedelta

import numpy as np
from pyvrp.stop import MaxRuntime

from waste.classes import Event, Route, ShiftPlanEvent, Simulator
from waste.functions import make_model

logger = logging.getLogger(__name__)


class BaselineStrategy:
    """
    A faithful implementation of what the municipality is currently doing.

    Parameters
    ----------
    sim
        The simulation environment.
    deposit_volume
        Assumed volume of the deposit with each arrival. This allows us to
        translate the number of arrivals into a total volume, and thus
        determine (as a rule-of-thumb) when a cluster will be full.
    num_clusters
        Number of clusters to schedule.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    perfect_information
        Whether to use perfect information of the current cluster volumes
        when deciding which clusters to visit. Default False.
    """

    def __init__(
        self,
        sim: Simulator,
        deposit_volume: float,
        num_clusters: int,
        max_runtime: float,
        perfect_information: bool = False,
        **kwargs,
    ):
        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        if num_clusters < 0:
            raise ValueError("Expected num_clusters >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.deposit_volume = deposit_volume
        self.num_clusters = num_clusters
        self.max_runtime = max_runtime
        self.perfect_information = perfect_information

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        cluster_idcs = self._get_cluster_idcs()
        model = make_model(self.sim, event, cluster_idcs)  # type: ignore

        result = model.solve(
            stop=MaxRuntime(self.max_runtime),
            seed=self.sim.generator.integers(100),
        )

        if not result.is_feasible():
            msg = f"Shiftplan at time {event.time} is infeasible!"
            logger.error(msg)
            raise RuntimeError(msg)

        return [
            Route(
                # PyVRP considers 0 the depot, and starts counting client
                # (cluster) indices from 1. So we need to subtract 1 from
                # the index returned by PyVRP before we map back to the
                # cluster indices.
                plan=[cluster_idcs[idx - 1] for idx in route],
                vehicle=self.sim.vehicles[route.vehicle_type()],
                start_time=event.time + timedelta(seconds=route.start_time()),
            )
            for route in result.best.get_routes()
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy

    def _get_cluster_idcs(self) -> np.ndarray[int]:
        clusters = self.sim.clusters

        if self.num_clusters >= len(clusters):
            return np.arange(0, len(clusters))

        # Step 1. Determine current volume in each cluster based on the current
        # number of arrivals. Or, when perfect information is used, just get
        # the actual current volume.
        if self.perfect_information:
            curr_vols = np.array([c.volume for c in clusters])
        else:
            arrivals = np.array([c.num_arrivals for c in clusters])
            curr_vols = self.deposit_volume * arrivals

        # Step 2. Determine the amount of time it'll take for each cluster to
        # fill up, given the current volume and the average arrival rate.
        capacities = np.array([c.corrected_capacity for c in clusters])
        max_extra = np.maximum(capacities - curr_vols, 0) / self.deposit_volume
        avg_rates = np.array([np.mean(c.rates) for c in clusters])

        # Divide max_extra / avg_rates, with some special precautions in case
        # avg_rates is zero somewhere (we set num_hours to +inf in that case).
        num_hours = np.full_like(curr_vols, fill_value=np.inf, dtype=float)
        num_hours = np.divide(
            max_extra,
            avg_rates,
            out=num_hours,
            where=~np.isclose(avg_rates, 0),
        )

        # Step 3. Select the ``num_clusters`` that will fill up the soonest.
        top_k = np.argpartition(num_hours, self.num_clusters)
        return top_k[: self.num_clusters]
