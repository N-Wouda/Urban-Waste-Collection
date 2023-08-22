import pytest
from numpy.random import default_rng
from numpy.testing import assert_raises

from waste.classes import Depot, Simulator
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
