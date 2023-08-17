from datetime import datetime

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_equal, assert_raises

from tests.helpers import dist
from waste.classes import Database, ShiftPlanEvent, Simulator
from waste.strategies import GreedyStrategy, RandomStrategy


@pytest.mark.parametrize(
    ("num_containers", "max_runtime"), [(-100, 0), (-1, 0), (0, -1.0)]
)
def test_init_raises_given_invalid_arguments(
    num_containers: int, max_runtime: float
):
    with assert_raises(ValueError):
        GreedyStrategy(num_containers, max_runtime)


@pytest.mark.parametrize(
    ("num_containers", "max_runtime"), [(0, 0), (0, 1), (1, 0), (100, 100)]
)
def test_init_does_not_raise_given_valid_arguments(
    num_containers: int, max_runtime: float
):
    GreedyStrategy(num_containers, max_runtime)


def test_raises_when_route_plan_is_infeasible():
    db = Database("tests/test.db", ":memory:", exists_ok=True)
    sim = Simulator(
        default_rng(seed=42),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    # We can never get to the first location in time: the total shift duration
    # is only eight hours, yet with this modification it takes ten hours to
    # get to location 1. There is no feasible route plan, and that should raise
    # an error.
    sim.durations[:, 1] = 36_000
    greedy = GreedyStrategy(num_containers=5, max_runtime=0.1)

    with assert_raises(RuntimeError):
        greedy(sim, ShiftPlanEvent(datetime.now()))


@pytest.mark.parametrize("num_containers", [1, 2, 5])
def test_routes_containers_with_most_arrivals(num_containers: int):
    db = Database("tests/test.db", ":memory:", exists_ok=True)
    sim = Simulator(
        default_rng(seed=42),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    num_arrivals = sim.generator.integers(100, size=(len(sim.containers)))
    for c, arrival in zip(sim.containers, num_arrivals):
        c.num_arrivals = arrival

    greedy = GreedyStrategy(num_containers=num_containers, max_runtime=0.1)
    res = greedy(sim, ShiftPlanEvent(datetime.now()))

    # There should be exactly num_containers in the route plan.
    actually_visited = {c for route in res for c in route.plan}
    assert_equal(len(actually_visited), num_containers)

    # The visited containers should be the ones with the highest number of
    # arrivals. The other containers should not be visited.
    sorted = np.argsort(-num_arrivals)
    selected, not_selected = sorted[:num_containers], sorted[num_containers:]
    assert_(all(c in actually_visited for c in selected))
    assert_(all(c not in actually_visited for c in not_selected))


def test_greedy_better_than_random():
    db = Database("tests/test.db", ":memory:", exists_ok=True)
    sim = Simulator(
        default_rng(seed=42),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    num_arrivals = sim.generator.integers(100, size=(len(sim.containers)))
    for c, arrival in zip(sim.containers, num_arrivals):
        c.num_arrivals = arrival

    # Four containers, or two containers per route (there are two vehicles, so
    # also two routes). This works out to the same solution size.
    greedy = GreedyStrategy(num_containers=4, max_runtime=0.5)
    random = RandomStrategy(containers_per_route=2)

    event = ShiftPlanEvent(datetime.now())
    greedy_res = greedy(sim, event)
    random_res = random(sim, event)

    # There's no guarantee that greedy is always better than random, but it's
    # pretty unlikely that that is not the case. Indeed, for this seed, it is
    # not.
    assert_(dist(sim.distances, greedy_res) < dist(sim.distances, random_res))
    assert_(greedy_res != random_res)
