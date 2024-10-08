from datetime import datetime, timedelta

import pytest
from numpy.random import default_rng
from numpy.testing import assert_allclose

from tests.helpers import MockStrategy, cum_value
from waste.classes import (
    Configuration,
    Event,
    Route,
    ShiftPlanEvent,
    Simulator,
)
from waste.measures import avg_route_duration


@pytest.mark.parametrize(
    "visits",
    [
        [],
        [[], []],
        [[], [1, 2]],
        [[1]],
        [[0], [1, 2]],
        [[0, 1], [2, 3]],
        [[1, 2, 3, 4]],
    ],
)
def test_for_routes_without_breaks(test_db, visits: list[list[int]]):
    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(
            BREAKS=tuple(),  # no breaks
            TIME_PER_CLUSTER=timedelta(minutes=0),
            TIME_PER_CONTAINER=timedelta(minutes=2),
        ),
    )

    now = datetime.now()
    routes = [Route(plan, veh, now) for plan, veh in zip(visits, sim.vehicles)]
    events: list[Event] = [ShiftPlanEvent(time=now)]
    sim(test_db.store, MockStrategy(sim, routes), events)

    # We're given a set of routes, and we already have a known-good helper for
    # computing the travel duration. When we add the actual number of stops,
    # the total duration should be the same.
    num_stops = sum(len(route) for route in routes)
    service_time = sim.config.TIME_PER_CONTAINER * num_stops
    helper_dur = cum_value(test_db.durations(), routes) + service_time
    avg_dur = helper_dur / max(len(routes), 1)
    assert_allclose(
        test_db.compute(avg_route_duration).total_seconds(),
        avg_dur.total_seconds(),
    )


@pytest.mark.parametrize(
    ("container_time", "break_time", "between"),
    [
        (timedelta(minutes=10), timedelta(minutes=0), (2, 3)),
        (timedelta(minutes=15), timedelta(minutes=5), (1, 2)),
        (timedelta(minutes=25), timedelta(minutes=30), (1, 2)),
    ],
)
def test_with_breaks(test_db, container_time, break_time, between):
    """
    Tests that the average route duration also takes into account any breaks
    that were had during the route, which require travel back to the depot.
    """
    now = datetime(2023, 8, 20, 8, 0, 0)
    hour = timedelta(hours=1)

    sim = Simulator(
        default_rng(0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
        Configuration(
            # Set up a break one hour into the shift, lasting break_time
            BREAKS=(((now + hour).time(), break_time),),
            TIME_PER_CLUSTER=timedelta(minutes=0),
            TIME_PER_CONTAINER=container_time,
        ),
    )

    # Single route plan visiting all five clusters three times. That takes
    # several hours, so the break should definitely be scheduled.
    routes = [Route([0, 1, 2, 3, 4] * 3, sim.vehicles[0], now)]
    sim(test_db.store, MockStrategy(sim, routes), [ShiftPlanEvent(time=now)])

    # The break is had between the given two location IDs. So we should have
    # additional duration of travelling back to the depot in between, minus
    # direct travel, plus the break.
    mat = test_db.durations()
    service_time = sim.config.TIME_PER_CONTAINER * len(routes[0])
    expected_dur = (
        cum_value(test_db.durations(), routes)
        + service_time
        + (mat[between[0], 0] + mat[0, between[1]]).item()
        - mat[*between].item()
        + break_time
    )
    measure_dur = test_db.compute(avg_route_duration)
    assert_allclose(measure_dur.total_seconds(), expected_dur.total_seconds())
