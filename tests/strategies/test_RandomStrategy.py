import pytest
from numpy.testing import assert_raises

from waste.strategies import RandomStrategy


@pytest.mark.parametrize("containers_per_route", [-100, -1])
def test_init_raises_given_invalid_arguments(containers_per_route: int):
    with assert_raises(ValueError):
        RandomStrategy(containers_per_route)


@pytest.mark.parametrize("containers_per_route", [0, 1, 100])
def test_init_does_not_raise_given_valid_arguments(containers_per_route: int):
    RandomStrategy(containers_per_route)
