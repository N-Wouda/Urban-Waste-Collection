from datetime import datetime, timedelta

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import NullStrategy
from waste.classes import (
    ArrivalEvent,
    Database,
    Event,
    ServiceEvent,
    Simulator,
)
from waste.measures import avg_service_level


@pytest.mark.parametrize(
    ("event_pattern", "volume", "expected"),
    [
        ("AAA", 10_000, 1.0),  # never serviced
        ("AS", 10_000, 0.0),  # overflowed
        ("AS", 4_000, 1.0),  # boundary: did not overflow, should be OK
        ("AAS", 2_000, 1.0),  # boundary: did not overflow, should be OK
        ("SAA", 10_000, 1.0),  # overflow after last service has no impact
        ("AAAS", 1_000, 1.0),  # below capacity
        ("AASASAS", 2_500, 2 / 3),  # first overflowed, last two did not
        ("ASSSS", 5_000, 3 / 4),  # first overflowed, last three did not
        ("", 0, 1.0),  # nothing happened
    ],
)
def test_single_container(event_pattern: str, volume: float, expected: float):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    container = sim.containers[0]
    assert_allclose(container.capacity, 4_000)

    now = datetime.now()
    events: list[Event] = []
    for hours, event_type in enumerate(event_pattern):
        # The pattern provides a sequence of service (S) and arrival (A) events
        # at the same container. We separate each event by an hour.
        time = now + timedelta(hours=hours)

        if event_type == "A":
            events.append(ArrivalEvent(time, sim.containers[0], volume=volume))
        else:
            # This slightly abuses the id_route because no route with ID 0
            # exists in the routes table, but that should be OK since we're
            # not testing routes here.
            events.append(
                ServiceEvent(
                    time,
                    timedelta(minutes=2),
                    0,
                    sim.containers[0],
                    sim.vehicles[0],
                )
            )

    sim(db.store, NullStrategy(sim), events)
    assert_allclose(db.compute(avg_service_level), expected)
