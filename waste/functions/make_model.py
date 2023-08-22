from collections import Counter
from typing import Optional

import numpy as np
from pyvrp import Model

from waste.classes import Simulator

from .f2i import f2i


def make_model(
    sim: Simulator,
    container_idcs: list[int],
    prizes: Optional[list[int]] = None,
    required: Optional[list[bool]] = None,
) -> Model:
    """
    Creates a PyVRP model instance with the given containers as clients, using
    data from the passed-in simulation environment.
    """
    if prizes is None:
        prizes = np.zeros_like(container_idcs, dtype=int)

    if required is None:
        required = np.ones_like(container_idcs, dtype=bool)

    time_per_container = sim.config.TIME_PER_CONTAINER
    shift_duration = sim.config.SHIFT_DURATION

    model = Model()
    model.add_depot(
        x=f2i(sim.depot.location[0]),
        y=f2i(sim.depot.location[1]),
        tw_late=int(shift_duration.total_seconds()),
    )

    for idx, container_idx in enumerate(container_idcs):
        container = sim.containers[container_idx]
        model.add_client(
            x=f2i(container.location[0]),
            y=f2i(container.location[1]),
            service_duration=int(time_per_container.total_seconds()),
            tw_late=int(shift_duration.total_seconds()),
            prize=prizes[idx],
            required=required[idx],
        )

    vehicle_count = Counter(int(v.capacity) for v in sim.vehicles)
    for capacity, num_available in vehicle_count.items():
        model.add_vehicle_type(capacity, num_available)

    # These are the full distance and duration matrices, but we are only
    # interested in the subset we are actually visiting. That subset is
    # given by the indices below.
    distances = sim.distances
    durations = sim.durations / np.timedelta64(1, "s")
    indices = [0] + [idx + 1 for idx in container_idcs]

    for frm_idx, frm in zip(indices, model.locations):
        for to_idx, to in zip(indices, model.locations):
            model.add_edge(
                frm,
                to,
                distances[frm_idx, to_idx],
                durations[frm_idx, to_idx],
            )

    return model
