from datetime import date

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose, assert_raises

from waste.classes import Database, Depot, Simulator
from waste.functions import generate_events
from waste.measures import avg_num_routes_per_day, avg_route_stops
from waste.strategies import PrizeCollectingStrategy


@pytest.mark.parametrize(
    ("rho", "threshold", "deposit_volume", "max_runtime"),
    [
        (-100, 0, 1, 0),
        (0, -100, 1, 0),
        (0, 0, 1, -100),
        (-1, 0, 1, 0),
        (0, -1, 1, 0),  # threshold < 0
        (0, 0, -1, 0),  # deposit_volume < 0
        (0, 0, 1, -1),
        (0, 1.5, 1, 0),  # threshold > 1
        (0, 0, 0, 0),  # deposit_volume = 0
    ],
)
def test_init_raises_given_invalid_arguments(
    rho: float, threshold: float, deposit_volume: float, max_runtime: float
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])

    with assert_raises(ValueError):
        PrizeCollectingStrategy(
            sim, rho, threshold, deposit_volume, max_runtime
        )


@pytest.mark.parametrize(
    ("rho", "threshold", "deposit_volume", "max_runtime"),
    [
        (0, 0, 1, 0),
        (0, 1, 1, 0),
    ],
)
def test_init_does_not_raise_given_edge_case_valid_arguments(
    rho: float, threshold: float, deposit_volume: float, max_runtime: float
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])
    PrizeCollectingStrategy(sim, rho, threshold, deposit_volume, max_runtime)


def test_zero_threshold_schedules_all_containers():
    """
    If the threshold value is zero, then all containers are always required.
    """
    db = Database("tests/test.db", ":memory:", exists_ok=True)
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    threshold = 0.0
    strategy = PrizeCollectingStrategy(sim, 1_000, threshold, 60, 0.05)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))

    # All containers must be visited, so the avg number of route stops times
    # the average number of routes should equal the number of containers (since
    # we simulate only a single day).
    avg_stops = db.compute(avg_route_stops)
    avg_num_routes = db.compute(avg_num_routes_per_day)
    assert_allclose(avg_stops * avg_num_routes, len(sim.containers))


@pytest.mark.filterwarnings("ignore::pyvrp.exceptions.EmptySolutionWarning")
@pytest.mark.parametrize(("rho", "expected"), [(0, 0), (1_000_000, 5)])
def test_prizes_determine_selected_containers(rho: float, expected: int):
    """
    When the prize scaling parameter rho is zero, no containers should be
    visited: the prize is zero. When the parameter is really large (in this
    test, one million), all containers should be visited.
    """
    db = Database("tests/test.db", ":memory:", exists_ok=True)
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = PrizeCollectingStrategy(sim, rho, 1.0, 60, 0.05)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))

    avg_stops = db.compute(avg_route_stops)
    avg_num_routes = db.compute(avg_num_routes_per_day)
    assert_allclose(avg_stops * avg_num_routes, expected)
