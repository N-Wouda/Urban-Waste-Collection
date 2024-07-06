from datetime import datetime

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_equal, assert_raises

from waste.classes import (
    Cluster,
    Depot,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY
from waste.strategies import BaselineStrategy


@pytest.mark.parametrize(
    ("deposit_volume", "num_clusters", "max_runtime"),
    [
        (0.0, 1, 1.0),
        (1.0, -100, 0),
        (1.0, -1, 0),
        (1.0, 0, -1.0),
        (-1.0, 1, 1.0),
    ],
)
def test_init_raises_given_invalid_arguments(
    deposit_volume: float, num_clusters: int, max_runtime: float
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])

    with assert_raises(ValueError):
        BaselineStrategy(sim, deposit_volume, num_clusters, max_runtime)


@pytest.mark.parametrize(
    ("deposit_volume", "num_clusters", "max_runtime"),
    [(1.0, 0, 0), (1.0, 0, 1), (1.0, 1, 0), (100, 100, 100)],
)
def test_init_does_not_raise_given_valid_arguments(
    deposit_volume: float, num_clusters: int, max_runtime: float
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])
    BaselineStrategy(sim, deposit_volume, num_clusters, max_runtime)


def test_strategy_with_a_lot_of_arrivals():
    """
    When clusters have *a lot* of arrivals, and should thus be considered
    full, they should show up in the routing decisions.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.where(np.eye(4), 0, 1),
        np.where(np.eye(4), 0, 1).astype(np.timedelta64(1, "s")),
        [
            Cluster("1", 1, [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Cluster("2", 2, [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Cluster("3", 3, [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        sim,
        deposit_volume=1.0,
        num_clusters=2,
        max_runtime=0.1,
    )

    for cluster in sim.clusters[:2]:  # only add arrivals to first two
        cluster.num_arrivals = 10_000

    # Only first two clusters have any arrivals (and a lot of them, too).
    # Since num_clusters = 2, only those two should show up in the routing
    # decisions.
    routes = baseline.plan(ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 2)
    assert_(0 in routes[0].plan)
    assert_(1 in routes[0].plan)


def test_strategy_considers_cluster_capacities():
    """
    Tests that the same number of arrivals does not mean the same for
    clusters of different capacities: the capacity is taken into account by
    the strategy.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.where(np.eye(4), 0, 1),
        np.where(np.eye(4), 0, 1).astype(np.timedelta64(1, "s")),
        [
            Cluster("1", 1, [0.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Cluster("2", 2, [0.0] * HOURS_IN_DAY, 2.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        sim,
        deposit_volume=1.0,
        num_clusters=1,
        max_runtime=0.1,
    )

    for cluster in sim.clusters:  # same number of arrivals for each
        cluster.num_arrivals = 2

    # Both clusters have seen two arrivals. But the second cluster has
    # double the capacity of the first. Since we can visit only a single
    # cluster, the baseline strategy should visit the smaller cluster.
    routes = baseline.plan(ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 1)
    assert_(0 in routes[0].plan)


def test_strategy_considers_cluster_arrival_rates():
    """
    In addition to cluster capacities, the strategy also takes into account
    the different average arrival rates at each cluster.
    """
    sim = Simulator(
        default_rng(0),
        Depot("depot", (0, 0)),
        np.where(np.eye(4), 0, 1),
        np.where(np.eye(4), 0, 1).astype(np.timedelta64(1, "s")),
        [
            Cluster("1", 1, [1.0] * HOURS_IN_DAY, 1.0, (0, 0)),
            Cluster("2", 2, [2.0] * HOURS_IN_DAY, 1.0, (0, 0)),
        ],
        [Vehicle("name", 1.0)],
    )

    baseline = BaselineStrategy(
        sim,
        deposit_volume=1.0,
        num_clusters=1,
        max_runtime=0.1,
    )

    # Neither cluster has seen any arrival. The second cluster fills up
    # twice as fast as the first cluster. Since we can visit only a single
    # cluster, we should prioritise the second one.
    routes = baseline.plan(ShiftPlanEvent(time=datetime.now()))
    assert_equal(len(routes), 1)
    assert_equal(len(routes[0]), 1)
    assert_(1 in routes[0].plan)
