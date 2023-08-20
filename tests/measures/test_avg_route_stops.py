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
from waste.measures import avg_route_stops


def test_avg_route_stops():
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
    # The PeriodicStrategy distributes the containers evenly over the vehicles.
    avg_stops_per_route = len(db.containers()) / len(db.vehicles())

    num_days = 1
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max) + timedelta(days=num_days)
    period = 2  # hours between two deposits

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

    assert_almost_equal(db.compute(avg_route_stops), avg_stops_per_route)
