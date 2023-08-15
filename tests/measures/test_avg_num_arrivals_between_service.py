from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd
from numpy.random import default_rng
from numpy.testing import assert_equal

from waste.classes import (
    ArrivalEvent,
    Container,
    Database,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY, SHIFT_PLAN_TIME
from waste.measures import avg_num_arrivals_between_service
from waste.strategies import RandomStrategy


def test_avg_arrivals_between_service():
    containers = [
        Container("test1", [1] * HOURS_IN_DAY, 1000.0, (53.0, 6.0)),
        Container("test2", [1] * HOURS_IN_DAY, 1000.0, (53.1, 6.1)),
    ]
    distances = np.array([[0, 1], [3, 0]], dtype=float)
    durations = np.array([[0, 1], [3, 0]], np.timedelta64(1, "s"))
    vehicles = [Vehicle("auto", 4000.0)]
    sim = Simulator(default_rng(0), distances, durations, containers, vehicles)

    src_db = ":memory:"
    res_db = ":memory:"
    db = Database(src_db, res_db)

    strategy = RandomStrategy(containers_per_route=2)

    # Generate deposits every other hour for two containers, starting from
    # 0h00. As the first shift starts at 7 am, there will be 4 deposits per
    # container for the first shift, and 12 deposits for the next. There the
    # average  number of deposits per shift must be (4 + 12)/2.
    average = (4 + 12) / 2

    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max) + timedelta(days=1)
    freq = "2H"  # frequency of deposits

    events = []
    for container in containers:
        deposit_times = pd.date_range(start, end, freq=freq).to_pydatetime()
        volumes = [10] * len(deposit_times)
        for t, volume in zip(deposit_times, volumes):
            events.append(ArrivalEvent(t, container=container, volume=volume))

    first_shift = datetime.combine(start.date(), SHIFT_PLAN_TIME)
    for t in pd.date_range(first_shift, end, freq="24H").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    sim(db.store, strategy, events)

    res = db.compute(avg_num_arrivals_between_service)
    assert_equal(res, average)
