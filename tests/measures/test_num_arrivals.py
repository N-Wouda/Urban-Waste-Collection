from datetime import date, datetime, time, timedelta

import pandas as pd
from numpy.random import default_rng

from tests.helpers import NullStrategy
from waste.classes import (
    ArrivalEvent,
    Container,
    Database,
    Simulator,
)
from waste.constants import HOURS_IN_DAY
from waste.measures import num_arrivals


def test_num_arrivals():
    containers = [
        Container("test1", [1] * HOURS_IN_DAY, 1000.0, (53.0, 6.0)),
        Container("test2", [1] * HOURS_IN_DAY, 1000.0, (53.1, 6.1)),
    ]

    sim = Simulator(default_rng(0), [], [], containers, [])

    src_db = "data/waste.db"
    res_db = ":memory:"
    db = Database(src_db, res_db)

    strategy = NullStrategy()

    # We generate for two full days one deposit every other hour for two
    # containers
    tot_events = 48 / 2 * 2

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

    sim(db.store, strategy, events)

    # Each of two containers generate 1 deposit every two hours
    res = db.compute(num_arrivals)

    assert len(events) == tot_events
    assert res == tot_events
