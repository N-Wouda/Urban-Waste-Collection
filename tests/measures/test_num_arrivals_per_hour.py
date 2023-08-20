from datetime import datetime, timedelta

import numpy as np
import pytest
from numpy.testing import assert_equal

from waste.classes import ArrivalEvent, Database
from waste.constants import HOURS_IN_DAY
from waste.measures import num_arrivals_per_hour


@pytest.mark.parametrize("num_events", [0, 1, 24, 25, 72, 73])
def test_single_container(num_events: int):
    db = Database("tests/test.db", ":memory:")
    containers = db.containers()

    now = datetime.now()
    histogram = np.zeros((HOURS_IN_DAY,))

    for hours in range(num_events):
        time = now + timedelta(hours=hours)
        histogram[time.hour] += 1

        event = ArrivalEvent(time, containers[0], volume=0.0)
        event.seal()
        db.store(event)

    res = db.compute(num_arrivals_per_hour)
    assert_equal(len(res), HOURS_IN_DAY)
    assert_equal(res, histogram)
