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
from waste.measures import avg_num_arrivals_between_service


def test_avg_arrivals_between_service():
    src_db = "tests/test.db"
    res_db = ":memory:"
    db = Database(src_db, res_db)

    sim = Simulator(
        default_rng(0),
        db.depot(),
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

    # Generate deposits every other hour for each container, starting from
    # 0h00. As the first shift starts at 7 am, there will be 4 deposits per
    # container for the first shift, and 12 deposits for each other day.
    average = (4 + 12 * num_days) / (num_days + 1)

    events = []
    for container in db.containers():
        deposit_times = pd.date_range(
            start, end, freq=f"{period}H"
        ).to_pydatetime()
        volumes = [10] * len(deposit_times)
        for t, volume in zip(deposit_times, volumes):
            events.append(ArrivalEvent(t, container=container, volume=volume))

    first_shift = datetime.combine(start.date(), sim.config.SHIFT_PLAN_TIME)
    for t in pd.date_range(first_shift, end, freq="24H").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    sim(db.store, strategy, events)

    res = db.compute(avg_num_arrivals_between_service)
    assert_almost_equal(res, average)
