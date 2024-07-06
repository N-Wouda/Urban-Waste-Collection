from datetime import datetime

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy
from waste.classes import (
    Configuration,
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
def test_for_single_shift(test_db, visits: list[list[int]]):
    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(BREAKS=tuple()),
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    strategy = MockStrategy(sim, routes)

    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(test_db.store, strategy, events)

    assert_allclose(test_db.compute(avg_num_routes_per_day), len(routes))
