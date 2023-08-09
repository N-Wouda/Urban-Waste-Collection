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

    # Create some initial events for the simulator. After creation, new events
    # are not yet sealed.
    init = [
        ArrivalEvent(time=0, container=container, volume=0),
        ServiceEvent(time=1, id_route=1, container=container, vehicle=1),
        ShiftPlanEvent(time=2),
    ]
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
    sim = Simulator(default_rng(0), [], [], [], [])
    init = [ShiftPlanEvent(time=time) for time in range(5, 0, -1)]

    stored = []
    sim(lambda event: stored.append(event), NullStrategy(), init)
    assert_equal(stored, sorted(stored, key=lambda event: event.time))
