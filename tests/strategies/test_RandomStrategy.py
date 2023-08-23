import pytest
from numpy.random import default_rng
from numpy.testing import assert_raises

from waste.classes import Depot, Simulator
from waste.strategies import RandomStrategy


@pytest.mark.parametrize("containers_per_route", [-100, -1])
def test_init_raises_given_invalid_arguments(containers_per_route: int):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])

    with assert_raises(ValueError):
        RandomStrategy(sim, containers_per_route)


@pytest.mark.parametrize("containers_per_route", [0, 1, 100])
def test_init_does_not_raise_given_valid_arguments(containers_per_route: int):
    sim = Simulator(default_rng(0), Depot("", (0, 0)), [], [], [], [])
    RandomStrategy(sim, containers_per_route)
