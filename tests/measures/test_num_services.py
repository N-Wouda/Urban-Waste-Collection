from datetime import datetime, timedelta

import pytest
from numpy.testing import assert_equal

from waste.classes import Database, ServiceEvent
from waste.measures import num_services


@pytest.mark.parametrize("num_events", [0, 1, 97])
def test_single_container(num_events: int):
    db = Database("tests/test.db", ":memory:")
    containers = db.containers()
    vehicles = db.vehicles()

    now = datetime.now()
    for hours in range(num_events):
        event = ServiceEvent(
            now + timedelta(hours=hours),
            timedelta(minutes=2),
            0,  # slight abuse of id_route, but should be OK
            containers[0],
            vehicles[0],
        )

        event.seal()
        db.store(event)

    assert_equal(db.compute(num_services), num_events)
