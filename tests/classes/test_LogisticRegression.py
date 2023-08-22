import pytest
from numpy.testing import assert_allclose

from waste.classes import Container, LogisticRegression
from waste.constants import HOURS_IN_DAY


@pytest.mark.parametrize(
    ("capacity", "deposit_volume", "eps"),
    [
        (4_000, 60, 1e-3),
        (6_000, 40, 1e-2),
        (100, 1, 1e-3),
        (1, 1, 1e-3),
        (1, 1, 1e-2),
    ],
)
def test_initial_params(capacity: float, deposit_volume: float, eps: float):
    container = Container("test", [0] * HOURS_IN_DAY, capacity, (0, 0))
    lr = LogisticRegression(container, deposit_volume, eps=eps)

    # Initially, the parameters are set such that p(0) = eps, and p(cap / vol)
    # = 1 - eps. This updates over time, with new observations.
    assert_allclose(lr.prob(0), eps)
    assert_allclose(lr.prob(capacity / deposit_volume), 1 - eps)


@pytest.mark.parametrize("obs_before_switch", [1, 5, 10])
def test_switch_to_actual_model_all_zero_obs(obs_before_switch: int):
    eps = 1e-3
    container = Container("test", [0] * HOURS_IN_DAY, 4_000, (0, 0))
    lr = LogisticRegression(container, 60, obs_before_switch, eps=eps)

    for _ in range(obs_before_switch):
        assert_allclose(lr.prob(0), eps)
        assert_allclose(lr.prob(container.capacity / 60), 1 - eps)

        lr.observe(0, False)

    # All our data is (0, False). It is then optimal to set all parameters to
    # zero, which gives a prediction of 1 / 2 everywhere.
    assert_allclose(lr.prob(-100), 0.5)
    assert_allclose(lr.prob(0), 0.5)
    assert_allclose(lr.prob(100), 0.5)
