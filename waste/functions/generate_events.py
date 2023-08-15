from datetime import date, datetime, time, timedelta

import pandas as pd

from waste.classes import ArrivalEvent, Event, ShiftPlanEvent, Simulator
from waste.constants import SHIFT_PLAN_TIME, VOLUME_RANGE


def generate_events(sim: Simulator, start: date, end: date) -> list[Event]:
    """
    Generates initial events for the simulator. This includes arrivals and the
    shift plan events.
    """
    start = datetime.combine(start, time(0, 0, 0))
    finish = datetime.combine(end, time(23, 59, 59))

    events: list[Event] = []
    for container in sim.containers:
        for now in pd.date_range(start, finish, freq="H").to_pydatetime():
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this container.
            num_deposits = sim.generator.poisson(container.rates[now.hour])
            time_offsets = sim.generator.uniform(size=num_deposits)
            volumes = sim.generator.uniform(*VOLUME_RANGE, size=num_deposits)

            for offset, volume in zip(time_offsets, volumes):
                events.append(
                    ArrivalEvent(
                        now + timedelta(hours=offset),
                        container=container,
                        volume=volume,
                    )
                )

    first_shift = datetime.combine(start, SHIFT_PLAN_TIME)
    for t in pd.date_range(first_shift, end, freq="D").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    return events
