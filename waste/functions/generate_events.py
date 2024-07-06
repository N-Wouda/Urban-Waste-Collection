from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

from waste.classes import (
    ArrivalEvent,
    Event,
    ServiceEvent,
    ShiftPlanEvent,
    Simulator,
)


def generate_events(
    sim: Simulator,
    start: date,
    end: date,
    seed_events: bool = False,
) -> list[Event]:
    """
    Generates initial events for the simulator. This includes arrivals and the
    shift plan events. Can also be used to create some "seed events", which are
    fake service events that may be helpful to seed a strategy. These seed
    events are fake, but are based on the same distributional assumptions as
    the arrivals.
    """
    volume_range = sim.config.VOLUME_RANGE

    earliest = datetime.combine(start, time.min)
    latest = datetime.combine(end, time.max)

    gen = sim.generator

    events: list[Event] = []
    first_shift = datetime.combine(start, sim.config.SHIFT_PLAN_TIME)
    for now in pd.date_range(first_shift, latest, freq="D").to_pydatetime():
        events.append(ShiftPlanEvent(now))

    for cluster in sim.clusters:
        for now in pd.date_range(earliest, latest, freq="H").to_pydatetime():
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this cluster.
            num_deposits = gen.poisson(cluster.rates[now.hour])
            time_offsets = gen.uniform(size=num_deposits)
            volumes = gen.triangular(*volume_range, num_deposits)

            for offset, volume in zip(time_offsets, volumes):
                events.append(
                    ArrivalEvent(
                        now + timedelta(hours=offset),
                        cluster=cluster,
                        volume=volume,
                    )
                )

        if seed_events:
            # Seed the strategy with some initial service events. These service
            # events are not real, but do reflect the underlying dynamics and
            # help cut down on the overall warm-up time.
            avg_volume = np.mean(sim.config.VOLUME_RANGE)
            stop = 2 * int(cluster.capacity / avg_volume + 1)

            for num_arrivals in np.arange(start=1, stop=stop):
                event = ServiceEvent(
                    time=datetime.min,
                    duration=timedelta(hours=0),
                    id_route=0,
                    cluster=cluster,
                    vehicle=sim.vehicles[0],
                )

                events.append(event)

                # TODO this isn't really pretty, but we need to avoid these
                # values being overwritten when the simulator again seals the
                # event, so we seal it here. Sealing is idempotent, so that's
                # not a problem, but we do need to explicitly define these
                # values.
                event.seal()

                event._num_arrivals = num_arrivals  # noqa: SLF001
                volumes = gen.triangular(*volume_range, num_arrivals)
                event._volume = sum(volumes[:num_arrivals])  # noqa: SLF001

    return events
