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
from waste.measures import avg_num_arrivals_between_service


@pytest.mark.parametrize(
    ("event_pattern", "expected"),
    [
        ("AASAS", 1.5),
        ("AAAS", 3.0),
        ("AAS", 2.0),
        ("ASASAS", 1.0),
        ("ASA", 1.0),
        ("SAA", 0.0),
        ("AAA", 0.0),
        ("", 0.0),
    ],
)
def test_for_single_cluster(test_db, event_pattern: str, expected: float):
    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(BREAKS=tuple()),
    )

    now = datetime.now()
    events: list[Event] = []
    for hours, event_type in enumerate(event_pattern):
        # The pattern provides a sequence of service (S) and arrival (A) events
        # at the same cluster. We separate each event by an hour.
        time = now + timedelta(hours=hours)

        if event_type == "A":
            events.append(ArrivalEvent(time, sim.clusters[0], volume=0.0))
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
    assert_allclose(
        test_db.compute(avg_num_arrivals_between_service), expected
    )
