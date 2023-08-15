from datetime import date, datetime

import numpy as np
import pandas as pd
from numpy.random import default_rng

from waste.classes import (
    ArrivalEvent,
    Container,
    Database,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY, SHIFT_PLAN_TIME
from waste.measures import (
    avg_num_arrivals_between_service,
)
from waste.strategies import RandomStrategy


def test_avg_arrivals_between_service():
    containers = [
        Container("test1", [1] * HOURS_IN_DAY, 1000.0, (53.0, 6.0)),
        Container("test2", [1] * HOURS_IN_DAY, 1000.0, (53.1, 6.1)),
    ]
    distances = np.array([[0, 1], [3, 0]], dtype=float)
    durations = np.array([[0, 1], [3, 0]], dtype=float)
    durations = durations.astype(np.timedelta64(1, "s"))
    vehicles = [Vehicle("auto", 4000.0)]
    sim = Simulator(default_rng(0), distances, durations, containers, vehicles)

    start = date(2023, 8, 9)
    end = date(2023, 8, 10)

    src_db = "data/waste.db"
    res_db = ":memory:"
    db = Database(src_db, res_db, exists_ok=True)

    strategy = RandomStrategy(containers_per_route=2)

    events = []
    for container in containers:
        deposit_times = pd.date_range(
            start, end, freq="2H", inclusive="left"
        ).to_pydatetime()
        volumes = [10] * len(deposit_times)
        for t, volume in zip(deposit_times, volumes):
            events.append(ArrivalEvent(t, container=container, volume=volume))

    first_shift = datetime.combine(start, SHIFT_PLAN_TIME)
    for t in pd.date_range(first_shift, end, freq="24H").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    sim(db.store, strategy, events)

    res = db.compute(avg_num_arrivals_between_service)
    print(res)
