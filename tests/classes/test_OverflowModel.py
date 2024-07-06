import numpy as np
from numpy.testing import assert_, assert_allclose

from waste.classes import Cluster, OverflowModel
from waste.constants import HOURS_IN_DAY


def test_zero():
    cluster = Cluster("test", 0, [0] * HOURS_IN_DAY, 1, (0, 0))
    model = OverflowModel(cluster)
    assert_(np.isclose(model.prob_arrivals(0), 0))


def test_rates():
    cluster = Cluster("test", 0, [1] * HOURS_IN_DAY, 2, (0, 0))
    model = OverflowModel(cluster, bounds=((1, 2), (1, 5)))

    model.observe(1, False)
    model.observe(2, True)
    model.observe(2, True)
    model.observe(3, True)

    assert_allclose(model.prob_arrivals(1, rate=0), 0.44, rtol=1e-2)

    assert_allclose(model.prob_arrivals(1, rate=2), 0.87, rtol=1e-2)
    assert_allclose(model.prob_arrivals(2, rate=1), 0.92, rtol=1e-2)
    assert_allclose(model.prob_arrivals(3, rate=0), 0.98, rtol=1e-2)


def test_volume():
    cluster = Cluster("test", 0, [1] * HOURS_IN_DAY, 2, (0, 0))
    model = OverflowModel(cluster, bounds=((1, 2), (1, 5)))

    # Known full at these volumes, and thus overflow probability should be 1
    # (since any additional stuff would cause an overflow).
    assert_allclose(model.prob_volume(2, rate=3), 1)
    assert_allclose(model.prob_volume(3, rate=3), 1)


def test_predict_boundary_cases():
    cluster = Cluster("test", 0, [0] * HOURS_IN_DAY, 5_000, (0, 0))
    model = OverflowModel(cluster)

    # There's no data, so the model assumes sensible defaults based on the
    # default bounds. This ensures p(0) == 0 and p(LARGE) = 1.
    assert_allclose(model.prob_arrivals(0), 0)
    assert_allclose(model.prob_arrivals(250), 1)
    assert_allclose(model.prob_arrivals(1000), 1)
