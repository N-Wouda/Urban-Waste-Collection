from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from pyvrp import Model

from waste.classes import ShiftPlanEvent, Simulator, Vehicle

from .f2i import f2i


def make_model(
    sim: Simulator,
    event: ShiftPlanEvent,
    cluster_idcs: list[int],
    prizes: Optional[list[int]] = None,
    required: Optional[list[bool]] = None,
    vehicles: Optional[list[Vehicle]] = None,
    shift_duration: Optional[timedelta] = None,
) -> Model:
    """
    Creates a PyVRP model instance with the given clusters as clients, using
    data from the passed-in simulation environment.
    """
    if prizes is None:
        prizes = [0] * len(cluster_idcs)

    if required is None:
        required = [True] * len(cluster_idcs)

    if shift_duration is None:
        shift_duration = sim.config.SHIFT_DURATION

    model = Model()
    model.add_depot(
        x=f2i(sim.depot.location[0]),
        y=f2i(sim.depot.location[1]),
        tw_late=int(shift_duration.total_seconds()),
    )

    for idx, cluster_idx in enumerate(cluster_idcs):
        cluster = sim.clusters[cluster_idx]
        tw_late = datetime.combine(event.time.date(), cluster.tw_late)
        assert tw_late >= event.time

        service_duration = (
            sim.config.TIME_PER_CLUSTER
            + cluster.num_containers * sim.config.TIME_PER_CONTAINER
        )

        last_moment = min(tw_late - event.time, shift_duration)
        model.add_client(
            x=f2i(cluster.location[0]),
            y=f2i(cluster.location[1]),
            service_duration=int(service_duration.total_seconds()),
            tw_late=int(last_moment.total_seconds()),
            prize=prizes[idx],
            required=required[idx],
        )

    for vehicle in vehicles if vehicles else sim.vehicles:
        start_time = datetime.combine(event.time.date(), vehicle.shift_start)
        end_time = datetime.combine(event.time.date(), vehicle.shift_end)
        assert end_time >= start_time

        model.add_vehicle_type(
            tw_early=int(max((start_time - event.time).total_seconds(), 0)),
            tw_late=int(max((end_time - event.time).total_seconds(), 0)),
        )

    # These are the full distance and duration matrices, but we are only
    # interested in the subset we are actually visiting. That subset is
    # given by the indices below.
    distances = sim.distances
    durations = sim.durations / np.timedelta64(1, "s")
    indices = [0] + [idx + 1 for idx in cluster_idcs]

    for frm_idx, frm in zip(indices, model.locations):
        for to_idx, to in zip(indices, model.locations):
            model.add_edge(
                frm,
                to,
                distances[frm_idx, to_idx],
                durations[frm_idx, to_idx],
            )

    return model
