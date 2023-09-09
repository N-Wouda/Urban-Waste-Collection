import pytest
from numpy.testing import assert_allclose

from waste.classes import Container, OverflowModel
from waste.constants import HOURS_IN_DAY


@pytest.mark.parametrize(
    ("capacity", "deposit_volume"),
    [
        (4_000, 60),
        (6_000, 40),
        (100, 1),
        (10, 1),
    ],
)
def test_initial_params(capacity: float, deposit_volume: float):
    container = Container("test", [0] * HOURS_IN_DAY, capacity, (0, 0))
    model = OverflowModel(container, deposit_volume)

    # Initially, the parameters are set such that p(0) = 0, and p(cap / vol)
    # = 1. This updates over time, with new observations.
    assert_allclose(model.prob(0), 0)
    assert_allclose(model.prob(capacity / deposit_volume), 1)


def test_predict():
    container = Container("test", [0] * HOURS_IN_DAY, 5_000, (0, 0))
    model = OverflowModel(container, 50)

    # Without data, the model starts from p(0) = 0, and p(cap / vol) = 1. It
    # linearly interpolates between those two values.
    assert_allclose(model.prob(0), 0)
    assert_allclose(model.prob(50), 0.5)
    assert_allclose(model.prob(100), 1)

    # It returns 1 for values beyond cap / vol, and 0 for values below 0.
    assert_allclose(model.prob(-100), 0)
    assert_allclose(model.prob(150), 1)


def test_multiple_observations():
    container = Container("test", [0] * HOURS_IN_DAY, 5_000, (0, 0))
    model = OverflowModel(container, 50)

    model.observe(50, False)
    model.observe(75, True)
    model.observe(75, False)
    model.observe(100, True)
    model.observe(150, True)

    assert_allclose(model.prob(0), 0)
    assert_allclose(model.prob(75), 0.48, rtol=1e-2)
