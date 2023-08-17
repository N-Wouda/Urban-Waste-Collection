import pytest
from numpy.testing import assert_equal

from waste.functions import f2i


@pytest.mark.parametrize("scale", [10, 100, 1_000, 10_000])
def test_scaling(scale: int):
    assert_equal(f2i(1.0, scale=scale), int(1.0 * scale))
    assert_equal(f2i(1.5, scale=scale), int(1.5 * scale))
    assert_equal(f2i(2.0, scale=scale), int(2.0 * scale))


def test_rounding():
    # Default scaled by 10K and round. That means we lose some precision, but
    # that can be avoided by increasing the scaling factor.
    assert_equal(f2i(1.00001), 10_000)
    assert_equal(f2i(1.00001, scale=100_000), 100_001)

    # This is not a problem for floating point values of lower precision.
    assert_equal(f2i(1.49), 14_900)
    assert_equal(f2i(1.5), 15_000)
