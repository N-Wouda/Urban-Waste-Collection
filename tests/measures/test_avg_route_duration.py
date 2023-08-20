from datetime import datetime, timedelta

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy, cum_value
from waste.classes import (
    Configuration,
    Database,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import avg_route_duration


@pytest.mark.parametrize(
    "visits",
    [
        [],
        [[], []],
        [[], [1, 2]],
        [[1]],
        [[0], [1, 2]],
        [[0, 1], [2, 3]],
        [[1, 2, 3, 4]],
    ],
)
def test_for_routes_without_breaks(visits: list[list[int]]):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
        Configuration(
            BREAKS=tuple(),  # no breaks
            TIME_PER_CONTAINER=timedelta(minutes=2),
        ),
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, MockStrategy(routes), events)

    # We're given a set of routes, and we already have a known-good helper for
    # computing the travel duration. When we add the actual number of stops,
    # the total duration should be the same.
    num_stops = sum(len(route) for route in routes)
    service_time = sim.config.TIME_PER_CONTAINER * num_stops
    helper_dur = cum_value(db.durations(), routes) + service_time
    avg_dur = helper_dur / max(len(routes), 1)
    assert_allclose(
        db.compute(avg_route_duration).total_seconds(), avg_dur.total_seconds()
    )


def test_with_breaks():
    """
    Tests that the average route distance also takes into account any breaks
    that were had during the route, which require travel back to the depot.
    """
    now = datetime.now()

    # Set up a half-hour break one hour into the shift.
    hour = timedelta(hours=1)
    a_break = (now + hour).time(), (now + 2 * hour).time(), hour / 2

    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
        Configuration(
            BREAKS=(a_break,),
            TIME_PER_CONTAINER=timedelta(minutes=10),
        ),
    )

    # Single route plan visiting all five containers three times. That takes
    # several hours, so the break should definitely be scheduled.
    routes = [Route([0, 1, 2, 3, 4] * 3, sim.vehicles[0], now)]
    sim(db.store, MockStrategy(routes), [ShiftPlanEvent(time=now)])

    service_time = sim.config.TIME_PER_CONTAINER * len(routes[0])
    helper_dur = cum_value(db.durations(), routes) + service_time
    measure_dur = db.compute(avg_route_duration)

    # Lets now compare numbers. The break is had after visiting container 1911
    # (location ID 1), before visiting container 2488 (ID 2). So we should have
    # additional duration of travelling 1 -> 0 -> 2, minus 1 -> 2, and taking
    # the break.
    mat = db.durations()
    diff = (mat[1, 0] + mat[0, 2] - mat[1, 2]).item() + hour / 2
    assert_allclose(
        measure_dur.total_seconds(), (helper_dur + diff).total_seconds()
    )
