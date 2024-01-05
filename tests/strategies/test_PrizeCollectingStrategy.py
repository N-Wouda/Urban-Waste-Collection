from datetime import date

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose, assert_equal, assert_raises

from waste.classes import Database, Depot, Simulator
from waste.constants import HOURS_IN_DAY
from waste.functions import generate_events
from waste.measures import avg_route_stops
from waste.strategies import PrizeCollectingStrategy


@pytest.mark.parametrize(
    ("rho", "deposit_volume", "max_runtime", "max_reused_solutions"),
    [
        (-100, 1, 0, 0),
        (0, 1, -100, 0),
        (-1, 1, 0, 0),
        (0, -1, 0, 0),  # deposit_volume < 0
        (0, 1, -1, 0),
        (0, 0, 0, 0),  # deposit_volume = 0
        (0, 1, 1, -1),  # max_reused_solutions < 0
    ],
)
def test_init_raises_given_invalid_arguments(
    rho: float,
    deposit_volume: float,
    max_runtime: float,
    max_reused_solutions: int,
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])

    with assert_raises(ValueError):
        PrizeCollectingStrategy(
            sim,
            rho,
            deposit_volume,
            max_runtime,
            max_reused_solutions,
        )


@pytest.mark.filterwarnings("ignore::pyvrp.exceptions.EmptySolutionWarning")
@pytest.mark.parametrize(("rho", "expected"), [(0, 0), (1_000_000, 4)])
def test_prizes_determine_selected_containers(rho: float, expected: int):
    """
    When the prize scaling parameter rho is zero, no containers should be
    visited: the prize is zero. When the parameter is larger, more containers
    should be visited.
    """
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = PrizeCollectingStrategy(sim, rho, 60, 0.05)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))

    # All containers must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(db.compute(avg_route_stops), expected)


@pytest.mark.parametrize("containers", [[0, 1], [3]])
def test_predicted_full_containers_are_visited(containers: list[int]):
    """
    This test checks that containers which are predicted to be full must be
    visited by the prize collecting strategy.
    """
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    for container in sim.containers:
        # The probability estimates are forward looking, taking into account
        # that the container might fill up before the next shift plan event.
        # We want to avoid that by setting the rates to zero.
        container.rates = [0] * HOURS_IN_DAY

    for idx in containers:
        sim.containers[idx].num_arrivals = 150

    strategy = PrizeCollectingStrategy(sim, 0, 60, 0.1)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))

    # All containers must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(db.compute(avg_route_stops), len(containers))


def test_visit_required_containers():
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    for container in sim.containers:
        # The probability estimates are forward looking, taking into account
        # that the container might fill up before the next shift plan event.
        # We want to avoid that by setting the rates to zero.
        container.rates = [0] * HOURS_IN_DAY

    # This ensures at least the first two containers will be visited. Since
    # the other containers start empty, they will not be visited, and we expect
    # two stops on a single route.
    sim.containers[0].num_arrivals = 150
    sim.containers[1].num_arrivals = 150

    strategy = PrizeCollectingStrategy(sim, 0, 60, 0.1)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))

    # All containers must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(db.compute(avg_route_stops), 2)


@pytest.mark.filterwarnings("ignore::pyvrp.exceptions.EmptySolutionWarning")
@pytest.mark.parametrize(("rho", "expected"), [(0, 0), (10_000, 3)])
def test_forward_looking_behaviour(rho: float, expected: int):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=42),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    for container in sim.containers:
        assert_equal(container.num_arrivals, 0)

    # The containers have zero arrivals, so any prizes/required visits must be
    # entirely based on some sort of forecast.
    strategy = PrizeCollectingStrategy(sim, rho, 60, 0.1)
    sim(db.store, strategy, generate_events(sim, date.today(), date.today()))
    assert_allclose(db.compute(avg_route_stops), expected)
