from datetime import datetime
from typing import Optional

import numpy as np
from pyvrp import Model

from waste.classes import ShiftPlanEvent, Simulator, Vehicle

from .f2i import f2i


def make_model(
    sim: Simulator,
    event: ShiftPlanEvent,
    container_idcs: list[int],
    prizes: Optional[list[int]] = None,
    required: Optional[list[bool]] = None,
    vehicles: Optional[list[Vehicle]] = None,
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
        tw_late = datetime.combine(event.time.date(), container.tw_late)
        assert tw_late >= event.time

        last_moment = min(tw_late - event.time, shift_duration)
        model.add_client(
            x=f2i(container.location[0]),
            y=f2i(container.location[1]),
            service_duration=int(time_per_container.total_seconds()),
            tw_late=int(last_moment.total_seconds()),
            prize=prizes[idx],
            required=required[idx],
        )

    for vehicle in vehicles if vehicles else sim.vehicles:
        start_time = datetime.combine(event.time.date(), vehicle.shift_start)
        end_time = datetime.combine(event.time.date(), vehicle.shift_end)

        model.add_vehicle_type(
            0,
            vehicle.num_available,
            tw_early=int(max((start_time - event.time).total_seconds(), 0)),
            tw_late=int(max((end_time - event.time).total_seconds(), 0)),
        )

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
