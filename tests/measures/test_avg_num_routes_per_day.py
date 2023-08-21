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
from waste.measures import avg_num_routes_per_day


@pytest.mark.parametrize(
    "visits",
    [
        [],  # no routes
        [[], [1]],  # 2 routes (one empty)
        [[0], [1, 2]],  # 2 routes
        [[0], [1], [2]],  # 3 routes
    ],
)
def test_for_single_shift(visits: list[list[int]]):
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

    assert_allclose(db.compute(avg_num_routes_per_day), len(routes))
