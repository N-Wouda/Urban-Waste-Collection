from datetime import datetime, timedelta

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_allclose

from tests.helpers import MockStrategy, dist
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
    strategy = MockStrategy(routes)

    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, strategy, events)

    # We're given a set of routes, and we already have a known-good helper for
    # computing the distance. Let's check the measure computes the same thing.
    avg_dist = dist(db.distances(), routes) / max(len(routes), 1)
    assert_allclose(db.compute(avg_route_distance), avg_dist)


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
        Configuration(BREAKS=(a_break,)),
    )

    # Single route plan visiting all five containers three times. That takes
    # several hours, so the break should definitely be scheduled.
    routes = [Route([0, 1, 2, 3, 4] * 3, sim.vehicles[0], now)]
    strategy = MockStrategy(routes)

    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, strategy, events)

    # First check that the total distance returned by avg_route_distance is
    # indeed not the same as our simple helper would suggest, since the latter
    # does not know about breaks.
    measure_dist = db.compute(avg_route_distance)
    helper_dist = dist(db.distances(), routes)
    assert_(not np.isclose(measure_dist, helper_dist))

    # Lets now compare numbers. The break is had after visiting container 1911
    # (location ID 1), before visiting container 2488 (location ID 2). So we
    # should have additional distance of travelling 1 -> 0 -> 2, while not
    # travelling 1 -> 2.
    mat = db.distances()
    diff = mat[1, 0] + mat[0, 2] - mat[1, 2]
    assert_allclose(measure_dist, helper_dist + diff)
