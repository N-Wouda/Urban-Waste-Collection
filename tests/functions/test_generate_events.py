from collections import Counter
from datetime import date, timedelta

import numpy as np
from numpy.testing import assert_, assert_allclose, assert_equal

from waste.classes import (
    ArrivalEvent,
    Container,
    Depot,
    ShiftPlanEvent,
    Simulator,
    Vehicle,
)
from waste.constants import HOURS_IN_DAY
from waste.functions import generate_events


def test_generates_shift_plan_events():
    today = date.today()
    tomorrow = today + timedelta(days=1)

    gen = np.random.default_rng(seed=42)
    depot = Depot("depot", (0, 0))
    sim = Simulator(gen, depot, [], [], [], [])

    # If the start and end date are the same, there is only a single shift plan
    # event. Additionally, because there are no containers in the simulator,
    # there also cannot be any arrival events.
    events = generate_events(sim, today, today)
    assert_equal(len(events), 1)
    assert_(isinstance(events[0], ShiftPlanEvent))
    assert_equal(events[0].time.time(), sim.config.SHIFT_PLAN_TIME)

    # A shift plan event is generated for each day in [start, end].
    events = generate_events(sim, today, tomorrow)
    assert_equal(len(events), 2)
    assert_(all(isinstance(event, ShiftPlanEvent)) for event in events)
    assert_(
        all(event.time.time() == sim.config.SHIFT_PLAN_TIME)
        for event in events
    )


def test_does_not_generate_arrivals_when_container_rates_are_zero():
    gen = np.random.default_rng(seed=42)
    container = Container("test", [0] * HOURS_IN_DAY, 0, (0.0, 0.0))
    depot = Depot("depot", (0, 0))
    sim = Simulator(gen, depot, [], [], [container], [])

    # Since the container's arrival rate is uniformly zero, no arrival events
    # should be generated. The only generated event from the call below is a
    # shift plan event.
    events = generate_events(sim, date.today(), date.today())
    assert_equal(len(events), 1)
    assert_(isinstance(events[0], ShiftPlanEvent))


def test_generates_arrival_events_based_on_container_rates():
    gen = np.random.default_rng(seed=42)

    # No arrivals in all hours, except in the first: there we have on average
    # 10 arrivals per hour.
    rates = [0] * HOURS_IN_DAY
    rates[0] = 10

    container = Container("test", rates, 0, (0.0, 0.0))
    depot = Depot("depot", (0, 0))
    sim = Simulator(gen, depot, [], [], [container], [])

    today = date.today()
    next_year = today.replace(year=today.year + 1)
    events = generate_events(sim, today, next_year)

    hours = [e.time.hour for e in events if isinstance(e, ArrivalEvent)]
    bins = Counter(hours)

    # There are arrivals in the first hour, but none in the other hours.
    assert_(bins[0] > 0)
    for hour in range(1, 24):
        assert_equal(bins[hour], 0)

    # We should have approximately ten arrivals per hour, and we have #days
    # hours. 5% tolerance because our dataset is not that large.
    assert_allclose(bins[0] / (next_year - today).days, 10, rtol=0.05)


def test_seed_events():
    gen = np.random.default_rng(seed=42)

    container = Container("test", [0] * HOURS_IN_DAY, 100, (0.0, 0.0))
    depot = Depot("depot", (0, 0))
    vehicle = Vehicle("test", 0)
    sim = Simulator(gen, depot, [], [], [container], [vehicle])

    no_seed = generate_events(sim, date.today(), date.today())
    seed = generate_events(sim, date.today(), date.today(), seed_events=True)

    # There should be more events when also seeding the strategy.
    assert_(len(seed) > len(no_seed))
