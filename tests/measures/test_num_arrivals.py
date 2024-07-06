from datetime import datetime, timedelta

import pytest
from numpy.testing import assert_equal

from waste.classes import ArrivalEvent
from waste.measures import num_arrivals


@pytest.mark.parametrize("num_events", [0, 1, 139])
def test_single_cluster(test_db, num_events: int):
    clusters = test_db.clusters()

    now = datetime.now()
    for hours in range(num_events):
        event = ArrivalEvent(
            now + timedelta(hours=hours),
            clusters[0],
            volume=0.0,
        )

        event.seal()
        test_db.store(event)

    assert_equal(test_db.compute(num_arrivals), num_events)
