from datetime import date, datetime, time, timedelta

import pandas as pd

from waste.classes import ArrivalEvent, Event, ShiftPlanEvent, Simulator


def generate_events(sim: Simulator, start: date, end: date) -> list[Event]:
    """
    Generates initial events for the simulator. This includes arrivals and the
    shift plan events.
    """
    earliest = datetime.combine(start, time.min)
    latest = datetime.combine(end, time.max)

    gen = sim.generator

    events: list[Event] = []
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

    first_shift = datetime.combine(start, sim.config.SHIFT_PLAN_TIME)
    for now in pd.date_range(first_shift, latest, freq="D").to_pydatetime():
        events.append(ShiftPlanEvent(now))

    return events
