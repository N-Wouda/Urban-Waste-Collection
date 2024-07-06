from datetime import datetime

import numpy as np
import pytest
from numpy.random import default_rng
from numpy.testing import assert_, assert_allclose, assert_equal

from waste.classes import ShiftPlanEvent, Simulator
from waste.functions import make_model


def test_required_and_prize_defaults(test_db):
    """
    Not passing prize or required fields should result in zero prizes, and all
    required clusters.
    """
    sim = Simulator(
        default_rng(seed=0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, np.arange(len(sim.clusters)))
    assert_(all(client.required) for client in model.locations)
    assert_allclose([client.prize for client in model.locations], 0)


@pytest.mark.parametrize("cluster_idcs", [[], [0, 1], [1], [1, 2, 3]])
def test_model_filters_by_given_clusters(test_db, cluster_idcs: list[int]):
    sim = Simulator(
        default_rng(seed=0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, cluster_idcs)
    assert_(len(model.locations), len(cluster_idcs) + 1)  # + depot


def test_creating_model_with_specified_vehicles(test_db):
    sim = Simulator(
        default_rng(seed=0),
        test_db.depot(),
        test_db.distances(),
        test_db.durations(),
        test_db.clusters(),
        test_db.vehicles(),
    )

    event = ShiftPlanEvent(datetime(2023, 8, 23, 7, 0, 0))
    model = make_model(sim, event, [0, 1, 2])
    assert_(len(sim.vehicles) > 1)
    assert_equal(len(model.vehicle_types), len(sim.vehicles))

    model = make_model(sim, event, [0, 1, 2], vehicles=sim.vehicles[:1])
    assert_equal(len(model.vehicle_types), 1)
