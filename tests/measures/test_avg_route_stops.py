from datetime import datetime

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy
from waste.classes import (
    Database,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import avg_route_stops


@pytest.mark.parametrize(
    ("visits", "expected"),
    [
        ([[0], [1, 2]], 1.5),  # 3 stops 2 routes: 1.5 average.
        ([[0, 1], [2, 3]], 2.0),  # 4 stops 2 routes: 2.0 average.
        ([[1]], 1.0),  # 1 stop 1 route: 1.0 average.
        ([[1, 2, 3, 4]], 4.0),  # 4 stops 1 route: 4.0 average.
        ([], 0.0),  # no routes: 0.0 average.
        ([[], [1, 2]], 1.0),  # 2 stops, 2 routes (one empty): 1.0 average.
    ],
)
def test_for_several_routes(visits: list[list[int]], expected: float):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    strategy = MockStrategy(sim, routes)

    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, strategy, events)

    # We're given a set of routes and the expected number of stops on those
    # routes. Now let's check the measure computes the same thing.
    assert_allclose(db.compute(avg_route_stops), expected)
