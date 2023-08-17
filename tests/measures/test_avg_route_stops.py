from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd
from numpy.random import default_rng
from numpy.testing import assert_equal

from tests.helpers import PeriodicStrategy
from waste.classes import (
    ArrivalEvent,
    Container,
    Database,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY, SHIFT_PLAN_TIME
from waste.measures import avg_route_stops


def test_avg_route_stops():
    num_vehicles = 3
    num_containers = 20
    vehicles = [Vehicle(f"a{i}", 4000.0) for i in range(num_vehicles)]
    containers = [
        Container(f"t{i}", [1] * HOURS_IN_DAY, 1000.0, (0, 0))
        for i in range(num_containers)
    ]

    durations = np.ones(
        (num_containers, num_containers), np.timedelta64(1, "s")
    )
    np.fill_diagonal(durations, 0)

    strategy = PeriodicStrategy()
    # The PeriodicStrategy distributes the containers evenly over the vehicles.
    avg_stops_per_route = num_containers / num_vehicles

    sim = Simulator(default_rng(0), [], durations, containers, vehicles)

    src_db = res_db = ":memory:"
    db = Database(src_db, res_db)

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

    first_shift = datetime.combine(start, SHIFT_PLAN_TIME)
    for t in pd.date_range(first_shift, end, freq="D").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    sim(db.store, strategy, events)

    assert_equal(db.compute(avg_route_stops), avg_stops_per_route)
