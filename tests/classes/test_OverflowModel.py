import numpy as np
from numpy.testing import assert_, assert_allclose

from waste.classes import Container, OverflowModel
from waste.constants import HOURS_IN_DAY


def test_zero():
    container = Container("test", [0] * HOURS_IN_DAY, 1, (0, 0))
    model = OverflowModel(container)
    assert_(np.isclose(model.prob(0), 0))


def test_rates():
    container = Container("test", [1] * HOURS_IN_DAY, 2, (0, 0))
    model = OverflowModel(container, bounds=((1, 2), (1, 5)))

    model.observe(1, False)
    model.observe(2, True)
    model.observe(2, True)
    model.observe(3, True)

    assert_allclose(model.prob(1, rate=0), 0.44, rtol=1e-2)

    assert_allclose(model.prob(1, rate=2), 0.87, rtol=1e-2)
    assert_allclose(model.prob(2, rate=1), 0.92, rtol=1e-2)
    assert_allclose(model.prob(3, rate=0), 0.98, rtol=1e-2)

    assert_allclose(model.prob(3, 0, rate=100), 1, rtol=1e-2)

    # Known full at these volumes, and thus overflow probability should be 1
    # (since any additional stuff would cause an overflow).
    assert_allclose(model.prob(0, 2, rate=3), 1)
    assert_allclose(model.prob(0, 3, rate=3), 1)


def test_predict_boundary_cases():
    container = Container("test", [0] * HOURS_IN_DAY, 5_000, (0, 0))
    model = OverflowModel(container)

    # There's no data, so the model assumes sensible defaults based on the
    # default bounds. This ensures p(0) == 0 and p(LARGE) = 1.
    assert_allclose(model.prob(0), 0)
    assert_allclose(model.prob(250), 1)
    assert_allclose(model.prob(1000), 1)
