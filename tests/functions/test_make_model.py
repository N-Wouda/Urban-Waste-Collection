from datetime import datetime

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_allclose, assert_equal

from waste.classes import Database, ShiftPlanEvent, Simulator
from waste.functions import make_model


def test_required_and_prize_defaults():
    """
    Not passing prize or required fields should result in zero prizes, and all
    required containers.
    """
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, np.arange(len(sim.containers)))
    assert_(all(client.required) for client in model.locations)
    assert_allclose([client.prize for client in model.locations], 0)


@pytest.mark.parametrize("container_idcs", [[], [0, 1], [1], [1, 2, 3]])
def test_model_filters_by_given_container_indices(container_idcs: list[int]):
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, container_idcs)
    assert_(len(model.locations), len(container_idcs) + 1)  # + depot


def test_creating_model_with_specified_vehicles():
    db = Database("tests/test.db", ":memory:")
    sim = Simulator(
        default_rng(seed=0),
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, [0, 1, 2])
    assert_(len(sim.vehicles) > 1)
    assert_equal(len(model.vehicle_types), len(sim.vehicles))

    model = make_model(sim, event, [0, 1, 2], vehicles=sim.vehicles[:1])
    assert_equal(len(model.vehicle_types), 1)
