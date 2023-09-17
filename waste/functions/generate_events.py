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
    earliest = datetime.combine(start, time.min)
    latest = datetime.combine(end, time.max)

    gen = sim.generator

    events: list[Event] = []
    first_shift = datetime.combine(start, sim.config.SHIFT_PLAN_TIME)
    for now in pd.date_range(first_shift, latest, freq="D").to_pydatetime():
        events.append(ShiftPlanEvent(now))

    for container in sim.containers:
        for now in pd.date_range(earliest, latest, freq="H").to_pydatetime():
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this container.
            num_deposits = gen.poisson(container.rates[now.hour])
            time_offsets = gen.uniform(size=num_deposits)
            volumes = gen.uniform(*sim.config.VOLUME_RANGE, size=num_deposits)

            for offset, volume in zip(time_offsets, volumes):
                events.append(
                    ArrivalEvent(
                        now + timedelta(hours=offset),
                        container=container,
                        volume=volume,
                    )
                )

        if seed_events:
            # Seed the strategy with some initial service events. These service
            # events are not real, but do reflect the underlying dynamics and
            # help cut down on the overall warm-up time.
            avg_volume = np.mean(sim.config.VOLUME_RANGE)
            stop = 2 * int(container.capacity / avg_volume + 1) + 10
            volumes = gen.uniform(*sim.config.VOLUME_RANGE, stop)

            for num_arrivals in np.arange(start=1, stop=stop, step=10):
                event = ServiceEvent(
                    time=datetime.min,
                    duration=timedelta(hours=0),
                    id_route=0,
                    container=container,
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
                event._volume = sum(volumes[:num_arrivals])  # noqa: SLF001

    return events
