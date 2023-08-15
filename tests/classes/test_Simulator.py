from datetime import datetime, timedelta

from numpy.random import default_rng
from numpy.testing import assert_, assert_equal

from tests.helpers import NullStrategy
from waste.classes import (
    ArrivalEvent,
    Container,
    ServiceEvent,
    ShiftPlanEvent,
    Simulator,
)
from waste.constants import HOURS_IN_DAY


def test_events_are_sealed_and_stored_property():
    container = Container("test", [1] * HOURS_IN_DAY, 1.0, (0.0, 0.0))
    sim = Simulator(default_rng(0), [], [], [container], [])

    now = datetime(2023, 8, 9, 10, 0, 0)

    # Create some initial events for the simulator.
    init = [
        ArrivalEvent(time=now, container=container, volume=0),
        ServiceEvent(
            time=now + timedelta(hours=1),
            id_route=1,
            container=container,
            vehicle=1,
        ),
        ShiftPlanEvent(time=now + timedelta(hours=2)),
    ]

    # After creation, new events are not yet sealed.
    for event in init:
        assert_(event.is_pending())
        assert_(not event.is_sealed())

    # Simulate and 'store' the sealed events to a list.
    stored = []
    sim(lambda event: stored.append(event), NullStrategy(), init)

    # Simulation should not have created any new events.
    assert_equal(len(init), len(stored))

    # All events should now be sealed, and no longer pending.
    for init_event, stored_event in zip(init, stored):
        assert_(init_event is stored_event)
        assert_(not init_event.is_pending())
        assert_(init_event.is_sealed())


def test_stored_events_are_sorted_in_time():
    now = datetime(2023, 8, 9)
    sim = Simulator(default_rng(0), [], [], [], [])
    init = [
        ShiftPlanEvent(time=now + timedelta(hours=hour))
        for hour in range(5, 0, -1)
    ]

    stored = []
    sim(lambda event: stored.append(event), NullStrategy(), init)
    assert_equal(stored, sorted(stored, key=lambda event: event.time))
