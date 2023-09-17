from datetime import datetime

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy
from waste.classes import (
    Configuration,
    Database,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import avg_route_clusters


@pytest.mark.parametrize(
    ("visits", "expected"),
    [
        ([], 0.0),  # no routes: 0.0 average.
        ([[1]], 1.0),  # one route: 1.0 average
        ([[1], []], 0.5),  # two routes, one empty: 0.5 average
        ([[1], [3, 4]], 1.0),  # 3 and 4 are in the same cluster: 1.0 average
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
        Configuration(BREAKS=tuple()),
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    strategy = MockStrategy(sim, routes)

    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(db.store, strategy, events)

    assert_allclose(db.compute(avg_route_clusters), expected)
