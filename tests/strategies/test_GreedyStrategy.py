import pytest
from numpy.testing import assert_raises

from waste.strategies import GreedyStrategy


@pytest.mark.parametrize(
    ("containers_per_route", "max_runtime"), [(-100, 0), (-1, 0), (0, -1.0)]
)
def test_init_raises_given_invalid_arguments(
    containers_per_route: int, max_runtime: float
):
    with assert_raises(ValueError):
        GreedyStrategy(containers_per_route, max_runtime)


@pytest.mark.parametrize(
    ("containers_per_route", "max_runtime"),
    [(0, 0), (0, 1), (1, 0), (100, 100)],
)
def test_init_does_not_raise_given_valid_arguments(
    containers_per_route: int, max_runtime: float
):
    GreedyStrategy(containers_per_route, max_runtime)
