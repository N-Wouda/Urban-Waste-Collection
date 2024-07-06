from datetime import datetime, timedelta

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_allclose

from tests.helpers import MockStrategy, cum_value
from waste.classes import (
    Configuration,
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
def test_for_routes_without_breaks(test_db, visits: list[list[int]]):
    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(BREAKS=tuple()),  # no breaks
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(test_db.store, MockStrategy(sim, routes), events)

    # We're given a set of routes, and we already have a known-good helper for
    # computing the distance. Let's check the measure computes the same thing.
    avg_dist = cum_value(test_db.distances(), routes) / max(len(routes), 1)
    assert_allclose(test_db.compute(avg_route_distance), avg_dist)


@pytest.mark.parametrize(
    "break_dur",
    [
        timedelta(seconds=1),  # it's not about the duration: any break *must*
        timedelta(seconds=5),  # be had, no matter how long.
    ],
)
def test_with_breaks(test_db, break_dur):
    """
    Tests that the average route distance also takes into account any breaks
    that were had during the route, which require travel back to the depot.
    """
    now = datetime(2023, 8, 20, 8, 0, 0)
    hour = timedelta(hours=1)

    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        # Set up a break one hour into the shift, lasting for the given time.
        Configuration(
            BREAKS=(((now + hour).time(), break_dur),),
            SHIFT_DURATION=timedelta(hours=8),
            TIME_PER_CONTAINER=timedelta(minutes=3),
        ),
    )

    # Single route plan visiting all five clusters three times. That takes
    # several hours, so the break should definitely be scheduled.
    routes = [Route([0, 1, 2, 3, 4] * 4, sim.vehicles[0], now)]
    strategy = MockStrategy(sim, routes)
    sim(test_db.store, strategy, [ShiftPlanEvent(time=now)])

    # First check that the total distance returned by avg_route_distance is
    # indeed not the same as our simple helper would suggest, since the latter
    # does not know about breaks.
    measure_dist = test_db.compute(avg_route_distance)
    helper_dist = cum_value(test_db.distances(), routes)
    assert_(not np.isclose(measure_dist, helper_dist))

    # Lets now compare numbers. The break is had after visiting cluster 1116
    # (location ID 4), before visiting test_db 1326 (ID 5). So we should have
    # additional distance of travelling 4 -> 0 -> 5, minus 4 -> 5.
    mat = test_db.distances()
    diff = mat[4, 0] + mat[0, 5] - mat[4, 5]
    assert_allclose(measure_dist, helper_dist + diff)
