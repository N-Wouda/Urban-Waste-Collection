from datetime import datetime, timedelta

import pytest
from numpy.testing import assert_equal

from waste.classes import ArrivalEvent, Database
from waste.measures import num_arrivals


@pytest.mark.parametrize("num_events", [0, 1, 139])
def test_single_container(num_events: int):
    db = Database("tests/test.db", ":memory:")
    containers = db.containers()

    now = datetime.now()
    for hours in range(num_events):
        event = ArrivalEvent(
            now + timedelta(hours=hours),
            containers[0],
            volume=0.0,
        )

        event.seal()
        db.store(event)

    assert_equal(db.compute(num_arrivals), num_events)
