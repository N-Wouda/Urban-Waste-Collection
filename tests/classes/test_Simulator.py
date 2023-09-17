from datetime import date, datetime, time, timedelta
from itertools import count

import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_equal

from tests.helpers import MockStrategy, NullStrategy
from waste.classes import (
    ArrivalEvent,
    BreakEvent,
    Configuration,
    Container,
    Database,
    Depot,
    Route,
    ServiceEvent,
    ShiftPlanEvent,
    Simulator,
)
from waste.constants import HOURS_IN_DAY
from waste.functions import generate_events


def test_events_are_sealed_and_stored_property():
    container = Container("test", [1] * HOURS_IN_DAY, 1.0, (0.0, 0.0))
    depot = Depot("depot", (0, 0))
    sim = Simulator(default_rng(0), depot, [], [], [container], [])

    now = datetime(2023, 8, 9, 10, 0, 0)

    # Create some initial events for the simulator.
    init = [
        ArrivalEvent(time=now, container=container, volume=0),
        ServiceEvent(
            time=now + timedelta(hours=1),
            duration=timedelta(seconds=0),
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
    sim(lambda event: stored.append(event), NullStrategy(sim), init)

    # Simulation should not have created any new events.
    assert_equal(len(init), len(stored))

    # All events should now be sealed, and no longer pending.
    for init_event, stored_event in zip(init, stored):
        assert_(init_event is stored_event)
        assert_(not init_event.is_pending())
        assert_(init_event.is_sealed())


def test_stored_events_are_sorted_in_time():
    now = datetime(2023, 8, 9)
    depot = Depot("depot", (0, 0))
    sim = Simulator(default_rng(0), depot, [], [], [], [])
    init = [
        ShiftPlanEvent(time=now + timedelta(hours=hour))
        for hour in range(5, 0, -1)
    ]

    stored = []
    sim(lambda event: stored.append(event), NullStrategy(sim), init)
    assert_equal(stored, sorted(stored, key=lambda event: event.time))


@pytest.mark.parametrize(
    ("start", "duration"),
    (
        (time(hour=8), timedelta(minutes=30)),
        (time(hour=7), timedelta(hours=1)),
        (time(hour=9), timedelta(minutes=15)),
    ),
)
def test_break_is_stored(start: time, duration: timedelta):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
        Configuration(BREAKS=((start, duration),)),
    )

    id_route = count(0)
    stored = []

    def mock_store(event):
        if isinstance(event, Route):
            return next(id_route)

        stored.append(event)
        return None

    # This strategy returns a single route with about 20 containers (visiting
    # the same four containers five times in a row). That takes about four
    # hours, so the break should be scheduled during that time.
    now = datetime(2023, 8, 18, 7, 0, 0)
    routes = [Route([1, 2, 3, 4] * 5, sim.vehicles[0], now)]
    strategy = MockStrategy(sim, routes)
    sim(mock_store, strategy, [ShiftPlanEvent(time=now)])

    stored_breaks = list(filter(lambda e: isinstance(e, BreakEvent), stored))
    assert_equal(len(stored_breaks), 1)
    assert_equal(stored_breaks[0].duration, duration)
    assert_equal(stored_breaks[0].time, datetime.combine(now.date(), start))


def test_observing_events():
    """
    Smoke test that checks the strategy gets to see all generated events.
    """
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    class Mock:
        def __init__(self, sim, **kwargs):
            pass

        def plan(self, *args, **kwargs):
            return []

        def observe(self, event):
            # Each observed event has already happened, so they should be
            # sealed by the time we get here.
            assert_(event.is_sealed())
            seen.append(event)

    seen = []
    init = generate_events(sim, date.today(), date.today() + timedelta(days=4))
    sim(lambda event: None, Mock(sim), init)

    # Should have seen all initial events. Since the mock strategy above does
    # not generate new events, the length of seen should correspond with init.
    assert_equal(len(seen), len(init))
