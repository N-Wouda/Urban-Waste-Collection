from numpy.testing import assert_, assert_equal

from tests.helpers import NullStrategy
from waste.classes import ArrivalEvent, Container, Simulator
from waste.constants import HOURS_IN_DAY


def test_events_are_sealed_and_stored_property():
    container = Container("test", [1] * HOURS_IN_DAY, 1.0, (0.0, 0.0))
    sim = Simulator([], [], [container], [])

    # Create some initial events for the simulator. After creation, new events
    # are not yet sealed.
    init = [ArrivalEvent(time, container, 0) for time in range(5)]
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