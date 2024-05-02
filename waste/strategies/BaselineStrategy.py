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
        determine (as a rule-of-thumb) when a container will be full.
    num_containers
        Number of containers to schedule.
    max_runtime
        Maximum runtime (in seconds) to use for route optimisation.
    perfect_information
        Whether to use perfect information of the current container's volumes
        when deciding which containers to visit. Default False.
    """

    def __init__(
        self,
        sim: Simulator,
        deposit_volume: float,
        num_containers: int,
        max_runtime: float,
        perfect_information: bool = False,
        **kwargs,
    ):
        if deposit_volume <= 0.0:
            raise ValueError("Expected deposit_volume > 0.")

        if num_containers < 0:
            raise ValueError("Expected num_containers >= 0.")

        if max_runtime < 0:
            raise ValueError("Expected max_runtime >= 0.")

        self.sim = sim
        self.deposit_volume = deposit_volume
        self.num_containers = num_containers
        self.max_runtime = max_runtime
        self.perfect_information = perfect_information

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        container_idcs = self._get_container_idcs()
        model = make_model(self.sim, event, container_idcs)  # type: ignore

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
                # (container) indices from 1. So we need to subtract 1 from
                # the index returned by PyVRP before we map back to the
                # container indices.
                plan=[container_idcs[idx - 1] for idx in route],
                vehicle=self.sim.vehicles[route.vehicle_type()],
                start_time=event.time + timedelta(seconds=route.start_time()),
            )
            for route in result.best.get_routes()
        ]

    def observe(self, event: Event):
        pass  # unused by this strategy

    def _get_container_idcs(self) -> np.ndarray[int]:
        containers = self.sim.containers

        if self.num_containers >= len(containers):
            return np.arange(0, len(containers))

        # Step 1. Determine current volume in each container based on the
        # current number of arrivals. Or, when perfect information is used,
        # just get the actual current volume.
        if self.perfect_information:
            curr_vols = np.array([c.volume for c in containers])
        else:
            arrivals = np.array([c.num_arrivals for c in containers])
            curr_vols = self.deposit_volume * arrivals

        # Step 2. Determine the amount of time it'll take for each container to
        # fill up, given the current volume and the average arrival rate.
        capacities = np.array([c.corrected_capacity for c in containers])
        max_extra = np.maximum(capacities - curr_vols, 0) / self.deposit_volume
        avg_rates = np.array([np.mean(c.rates) for c in containers])

        # Divide max_extra / avg_rates, with some special precautions in case
        # avg_rates is zero somewhere (we set num_hours to +inf in that case).
        num_hours = np.full_like(curr_vols, fill_value=np.inf, dtype=float)
        num_hours = np.divide(
            max_extra,
            avg_rates,
            out=num_hours,
            where=~np.isclose(avg_rates, 0),
        )

        # Step 3. Select the ``num_containers`` that will fill up the soonest.
        top_k = np.argpartition(num_hours, self.num_containers)
        return top_k[: self.num_containers]
