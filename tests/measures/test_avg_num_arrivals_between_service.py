from datetime import datetime, timedelta

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import NullStrategy
from waste.classes import (
    ArrivalEvent,
    Configuration,
    Database,
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
def test_for_single_container(event_pattern: str, expected: float):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
        Configuration(BREAKS=tuple()),
    )

    now = datetime.now()
    events: list[Event] = []
    for hours, event_type in enumerate(event_pattern):
        # The pattern provides a sequence of service (S) and arrival (A) events
        # at the same container. We separate each event by an hour.
        time = now + timedelta(hours=hours)

        if event_type == "A":
            events.append(ArrivalEvent(time, sim.containers[0], volume=0.0))
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
    assert_allclose(db.compute(avg_num_arrivals_between_service), expected)
