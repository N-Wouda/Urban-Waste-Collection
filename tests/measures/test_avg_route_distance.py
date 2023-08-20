from datetime import datetime, timedelta

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_allclose

from tests.helpers import MockStrategy, cum_value
from waste.classes import (
    Configuration,
    Database,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import avg_route_distance


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
        Configuration(BREAKS=tuple()),  # no breaks
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, MockStrategy(routes), events)

    # We're given a set of routes, and we already have a known-good helper for
    # computing the distance. Let's check the measure computes the same thing.
    avg_dist = cum_value(db.distances(), routes) / max(len(routes), 1)
    assert_allclose(db.compute(avg_route_distance), avg_dist)


@pytest.mark.parametrize(
    "break_time",
    [
        timedelta(seconds=1),  # it's not about the duration: any break *must*
        timedelta(minutes=5),  # be had, no matter how long.
    ],
)
def test_with_breaks(break_time):
    """
    Tests that the average route distance also takes into account any breaks
    that were had during the route, which require travel back to the depot.
    """
    now = datetime(2023, 8, 20, 8, 0, 0)
    hour = timedelta(hours=1)  # set up a break one hour into the shift
    a_break = (now + hour).time(), (now + 2 * hour).time(), break_time

    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
        Configuration(BREAKS=(a_break,)),
    )

    # Single route plan visiting all five containers three times. That takes
    # several hours, so the break should definitely be scheduled.
    routes = [Route([0, 1, 2, 3, 4] * 4, sim.vehicles[0], now)]
    strategy = MockStrategy(routes)
    sim(db.store, strategy, [ShiftPlanEvent(time=now)])

    # First check that the total distance returned by avg_route_distance is
    # indeed not the same as our simple helper would suggest, since the latter
    # does not know about breaks.
    measure_dist = db.compute(avg_route_distance)
    helper_dist = cum_value(db.distances(), routes)
    assert_(not np.isclose(measure_dist, helper_dist))

    # Lets now compare numbers. The break is had after visiting container 1911
    # (location ID 1), before visiting container 2488 (ID 2). So we should have
    # additional distance of travelling 1 -> 0 -> 2, minus 1 -> 2.
    mat = db.distances()
    diff = mat[1, 0] + mat[0, 2] - mat[1, 2]
    assert_allclose(measure_dist, helper_dist + diff)
