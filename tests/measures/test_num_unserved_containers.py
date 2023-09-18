from datetime import datetime

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy
from waste.classes import (
    Configuration,
    Database,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import num_unserved_containers


@pytest.mark.parametrize(
    ("visits", "expected"),
    [
        ([], 5),  # none visited
        ([1], 4),  # one visited
        ([1, 1, 1], 4),  # some container visited multiple times
        ([0, 1, 2, 3, 4], 0),  # all visited
    ],
)
def test_containers(visits: list[int], expected: int):
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
    strategy = MockStrategy(sim, [Route(visits, sim.vehicles[0], now)])
    sim(db.store, strategy, [ShiftPlanEvent(time=now)])

    # We're given a set of routes and the expected number of stops on those
    # routes. Now let's check the measure computes the same thing.
    assert_allclose(db.compute(num_unserved_containers), expected)
