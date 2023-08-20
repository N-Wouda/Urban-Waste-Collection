from datetime import datetime

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

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
        [[0], [1, 2]],
        [[0, 1], [2, 3]],
        [[1]],
        [[1, 2, 3, 4]],
        [],
        [[], [1, 2]],
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
    pass
