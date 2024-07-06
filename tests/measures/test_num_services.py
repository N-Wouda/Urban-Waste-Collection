from datetime import datetime, timedelta

import pytest
from numpy.testing import assert_equal

from waste.classes import ServiceEvent
from waste.measures import num_services


@pytest.mark.parametrize("num_events", [0, 1, 97])
def test_single_cluster(test_db, num_events: int):
    clusters = test_db.clusters()
    vehicles = test_db.vehicles()

    now = datetime.now()
    for hours in range(num_events):
        event = ServiceEvent(
            now + timedelta(hours=hours),
            timedelta(minutes=2),
            0,  # slight abuse of id_route, but should be OK
            clusters[0],
            vehicles[0],
        )

        event.seal()
        test_db.store(event)

    assert_equal(test_db.compute(num_services), num_events)
