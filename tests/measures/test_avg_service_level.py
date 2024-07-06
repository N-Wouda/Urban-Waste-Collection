from datetime import datetime, timedelta

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import NullStrategy
from waste.classes import (
    ArrivalEvent,
    Configuration,
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
def test_single_cluster(
    test_db, event_pattern: str, volume: float, expected: float
):
    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(BREAKS=tuple()),
    )

    cluster = sim.clusters[0]
    assert_allclose(cluster.capacity, 4_000)

    now = datetime.now()
    events: list[Event] = []
    for hours, event_type in enumerate(event_pattern):
        # The pattern provides a sequence of service (S) and arrival (A) events
        # at the same cluster. We separate each event by an hour.
        time = now + timedelta(hours=hours)

        if event_type == "A":
            events.append(ArrivalEvent(time, sim.clusters[0], volume=volume))
        else:
            # This slightly abuses the id_route because no route with ID 0
            # exists in the routes table, but that should be OK since we're
            # not testing routes here.
            events.append(
                ServiceEvent(
                    time,
                    timedelta(minutes=2),
                    0,
                    sim.clusters[0],
                    sim.vehicles[0],
                )
            )

    sim(test_db.store, NullStrategy(sim), events)
    assert_allclose(test_db.compute(avg_service_level), expected)
