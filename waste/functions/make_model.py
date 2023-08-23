from collections import Counter
from datetime import datetime
from typing import Optional

import numpy as np
from pyvrp import Model

from waste.classes import ShiftPlanEvent, Simulator

from .f2i import f2i


def make_model(
    sim: Simulator,
    event: ShiftPlanEvent,
    container_idcs: list[int],
    prizes: Optional[list[int]] = None,
    required: Optional[list[bool]] = None,
    plan_breaks: bool = False,
) -> Model:
    """
    Creates a PyVRP model instance with the given containers as clients, using
    data from the passed-in simulation environment.
    """
    if prizes is None:
        prizes = [0] * len(container_idcs)

    if required is None:
        required = [True] * len(container_idcs)

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

    if plan_breaks:
        # Then we plan breaks. These are new "clients" at the depot location,
        # one for each vehicle. We add edges from and to the real locations, so
        # that we can 'visit' the break from anywhere.
        size_no_breaks = len(model.locations)

        for early, late, duration in sim.config.BREAKS:
            early_today = datetime.combine(event.time.date(), early)
            late_today = datetime.combine(event.time.date(), late)

            for _ in sim.vehicles:
                model.add_client(
                    x=f2i(sim.depot.location[0]),
                    y=f2i(sim.depot.location[1]),
                    service_duration=int(duration.total_seconds()),
                    tw_early=int((early_today - event.time).total_seconds()),
                    tw_late=int((late_today - event.time).total_seconds()),
                    required=True,
                )

        for loc_idx, loc in zip(indices, model.locations[:size_no_breaks]):
            for brk in model.locations[size_no_breaks:]:
                model.add_edge(
                    loc,
                    brk,
                    distances[loc_idx, 0],
                    durations[loc_idx, 0],
                )

                model.add_edge(
                    brk,
                    loc,
                    distances[0, loc_idx],
                    durations[0, loc_idx],
                )

    return model
