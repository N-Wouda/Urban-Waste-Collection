from datetime import date, datetime, time, timedelta

import pandas as pd
from numpy.random import default_rng
from numpy.testing import assert_almost_equal

from tests.helpers import PeriodicStrategy
from waste.classes import (
    ArrivalEvent,
    Database,
    ShiftPlanEvent,
    Simulator,
)
from waste.constants import SHIFT_PLAN_TIME
from waste.measures import avg_service_level


def test_avg_service_levels():
    src_db = "tests/test.db"
    res_db = ":memory:"
    db = Database(src_db, res_db)

    sim = Simulator(
        default_rng(0),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = PeriodicStrategy()

    num_days = 2
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max) + timedelta(days=num_days)
    period = 2  # hours between two deposits
    deposit_vol = 500  # liters

    events = []
    for container in db.containers():
        deposit_times = pd.date_range(
            start, end, freq=f"{period}H"
        ).to_pydatetime()
        volumes = [deposit_vol] * len(deposit_times)
        for t, volume in zip(deposit_times, volumes):
            events.append(ArrivalEvent(t, container=container, volume=volume))

    first_shift = datetime.combine(start.date(), SHIFT_PLAN_TIME)
    num_shifts = 0
    for t in pd.date_range(first_shift, end, freq="24H").to_pydatetime():
        events.append(ShiftPlanEvent(t))
        num_shifts += 1

    sim(db.store, strategy, events)

    # On the first day, each container is emptied after 8 hours.
    first_day_volume = 8 / period * deposit_vol
    num_ok = sum(first_day_volume < c.capacity for c in db.containers())
    # On the other days day, each container is emptied after 24 hours.
    other_day_volume = 24 / period * deposit_vol
    for day in range(num_days):
        num_ok += sum(other_day_volume < c.capacity for c in db.containers())
    average = num_ok / num_shifts / len(db.containers())

    res = db.compute(avg_service_level)
    assert_almost_equal(res, average)
