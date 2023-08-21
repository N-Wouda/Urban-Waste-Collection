from datetime import date, datetime, timedelta

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_equal, assert_raises

from waste.classes import (
    Container,
    Database,
    Depot,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY
from waste.functions import generate_events
from waste.measures import (
    avg_route_distance,
    avg_service_level,
    num_arrivals,
    num_services,
)
from waste.strategies import BaselineStrategy, GreedyStrategy


@pytest.mark.parametrize(
    ("deposit_volume", "num_containers", "max_runtime"),
    [
        (0.0, 1, 1.0),
        (1.0, -100, 0),
        (1.0, -1, 0),
        (1.0, 0, -1.0),
        (-1.0, 1, 1.0),
    ],
)
def test_init_raises_given_invalid_arguments(
    deposit_volume: float, num_containers: int, max_runtime: float
):
    with assert_raises(ValueError):
        BaselineStrategy(deposit_volume, num_containers, max_runtime)


@pytest.mark.parametrize(
    ("deposit_volume", "num_containers", "max_runtime"),
    [(1.0, 0, 0), (1.0, 0, 1), (1.0, 1, 0), (100, 100, 100)],
)
def test_init_does_not_raise_given_valid_arguments(
    deposit_volume: float, num_containers: int, max_runtime: float
):
    BaselineStrategy(deposit_volume, num_containers, max_runtime)


def test_strategy_with_a_lot_of_arrivals():
    """
    When containers have *a lot* of arrivals, and should thus be considered
    full, they should show up in the routing decisions.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.ones((4, 4)),
        np.ones((4, 4)).astype(np.timedelta64(1, "s")),
        [
            Container("1", [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Container("2", [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Container("3", [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        deposit_volume=1.0,
        num_containers=2,
        max_runtime=0.1,
    )

    for container in sim.containers[:2]:  # only add arrivals to first two
        container.num_arrivals = 10_000

    # Only first two containers have any arrivals (and a lot of them, too).
    # Since num_containers = 2, only those two should show up in the routing
    # decisions.
    routes = baseline.plan(sim, ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 2)
    assert_(0 in routes[0].plan)
    assert_(1 in routes[0].plan)


def test_strategy_considers_container_capacities():
    """
    Tests that the same number of arrivals does not mean the same for
    containers of different capacities: the capacity is taken into account by
    the strategy.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.ones((4, 4)),
        np.ones((4, 4)).astype(np.timedelta64(1, "s")),
        [
            Container("1", [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Container("2", [0.0] * HOURS_IN_DAY, 2.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        deposit_volume=1.0,
        num_containers=1,
        max_runtime=0.1,
    )

    for container in sim.containers:  # same number of arrivals for each
        container.num_arrivals = 2

    # Both containers have seen two arrivals. But the second container has
    # double the capacity of the first. Since we can visit only a single
    # container, the baseline strategy should visit the smaller container.
    routes = baseline.plan(sim, ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 1)
    assert_(0 in routes[0].plan)


def test_strategy_considers_container_arrival_rates():
    """
    In addition to container capacities, the strategy also takes into account
    the different average arrival rates at each container.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.ones((4, 4)),
        np.ones((4, 4)).astype(np.timedelta64(1, "s")),
        [
            Container("1", [1.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Container("2", [2.0] * HOURS_IN_DAY, 1.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        deposit_volume=1.0,
        num_containers=1,
        max_runtime=0.1,
    )

    # Neither container has seen any arrival. The second container fills up
    # twice as fast as the first container. Since we can visit only a single
    # container, we should prioritise the second one.
    routes = baseline.plan(sim, ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 1)
    assert_(1 in routes[0].plan)


def test_baseline_not_greedy():
    """
    Smoke test that checks that the baseline strategy is not the same as the
    greedy strategy.
    """

    def simulate(db, strategy):
        """
        Simulates one week's worth of events, using the given database and
        strategy.
        """
        sim = Simulator(
            default_rng(0),
            db.depot(),
            db.distances(),
            db.durations(),
            db.containers(),
            db.vehicles(),
        )

        today = date.today()
        next_week = date.today() + timedelta(days=7)
        sim(db.store, strategy, generate_events(sim, today, next_week))

    db1 = Database("tests/test.db", ":memory:")
    db2 = Database("tests/test.db", ":memory:")

    # For baseline we also need to specify the deposit volume. Same runtime and
    # number of selected containers for both, to facilitate a fair comparison.
    simulate(db1, BaselineStrategy(60, num_containers=3, max_runtime=0.05))
    simulate(db2, GreedyStrategy(num_containers=3, max_runtime=0.05))

    # Test that both databases agree on the basic number of events.
    assert_equal(db1.compute(num_services), db2.compute(num_services))
    assert_equal(db1.compute(num_arrivals), db2.compute(num_arrivals))

    # But they should not have scheduled the same containers, so these
    # route-level statistics should differ.
    for measure in [avg_route_distance, avg_service_level]:
        assert_(not np.isclose(db1.compute(measure), db2.compute(measure)))
