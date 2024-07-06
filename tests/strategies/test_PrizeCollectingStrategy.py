from datetime import date

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose, assert_equal, assert_raises

from waste.classes import Depot, Simulator
from waste.constants import HOURS_IN_DAY
from waste.functions import generate_events
from waste.measures import avg_route_stops
from waste.strategies import PrizeCollectingStrategy


@pytest.mark.parametrize(("rho", "max_runtime"), [(-100, 0), (0, -100)])
def test_init_raises_given_invalid_arguments(
    rho: float,
    max_runtime: float,
):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])

    with assert_raises(ValueError):
        PrizeCollectingStrategy(sim, rho, max_runtime)


@pytest.mark.filterwarnings("ignore::pyvrp.exceptions.EmptySolutionWarning")
@pytest.mark.parametrize(("rho", "expected"), [(0, 0), (1_000_000, 4)])
def test_prizes_determine_selected_clusters(
    test_db, rho: float, expected: int
):
    """
    When the prize scaling parameter rho is zero, no clusters should be
    visited: the prize is zero. When the parameter is larger, more clusters
    should be visited.
    """
    sim = Simulator(
        default_rng(seed=42),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    sim(
        test_db.store,
        PrizeCollectingStrategy(sim, rho, 0.05, required_threshold=1.0),
        generate_events(sim, date.today(), date.today()),
    )

    # All clusters must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(test_db.compute(avg_route_stops), expected)


@pytest.mark.parametrize("clusters", [[0, 1], [3]])
def test_predicted_full_clusters_are_visited(test_db, clusters: list[int]):
    """
    This test checks that clusters which are predicted to be full must be
    visited by the prize collecting strategy.
    """
    sim = Simulator(
        default_rng(seed=42),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    for cluster in sim.clusters:
        # The probability estimates are forward looking, taking into account
        # that the cluster might fill up before the next shift plan event.
        # We want to avoid that by setting the rates to zero.
        cluster.rates = [0] * HOURS_IN_DAY

    for idx in clusters:
        sim.clusters[idx].num_arrivals = 150

    strategy = PrizeCollectingStrategy(sim, 0, 0.1)
    sim(
        test_db.store,
        strategy,
        generate_events(sim, date.today(), date.today()),
    )

    # All clusters must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(test_db.compute(avg_route_stops), len(clusters))


def test_visit_required_clusters(test_db):
    sim = Simulator(
        default_rng(seed=42),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    for cluster in sim.clusters:
        # The probability estimates are forward looking, taking into account
        # that the cluster might fill up before the next shift plan event.
        # We want to avoid that by setting the rates to zero.
        cluster.rates = [0] * HOURS_IN_DAY

    # This ensures at least the first two clusters will be visited. Since
    # the other clusters start empty, they will not be visited, and we expect
    # two stops on a single route.
    sim.clusters[0].num_arrivals = 150
    sim.clusters[1].num_arrivals = 150

    strategy = PrizeCollectingStrategy(sim, 0, 0.1)
    sim(
        test_db.store,
        strategy,
        generate_events(sim, date.today(), date.today()),
    )

    # All clusters must be visited, and that takes only a single vehicle, so
    # the average number of stops is the total number visited.
    assert_allclose(test_db.compute(avg_route_stops), 2)


@pytest.mark.filterwarnings("ignore::pyvrp.exceptions.EmptySolutionWarning")
@pytest.mark.parametrize(("rho", "expected"), [(0, 0), (10_000, 3)])
def test_forward_looking_behaviour(test_db, rho: float, expected: int):
    sim = Simulator(
        default_rng(seed=42),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    for cluster in sim.clusters:
        assert_equal(cluster.num_arrivals, 0)

    # The clusters have zero arrivals, so any prizes/required visits must be
    # entirely based on some sort of forecast.
    strategy = PrizeCollectingStrategy(sim, rho, 0.1, required_threshold=1.0)
    sim(
        test_db.store,
        strategy,
        generate_events(sim, date.today(), date.today()),
    )
    assert_allclose(test_db.compute(avg_route_stops), expected)
