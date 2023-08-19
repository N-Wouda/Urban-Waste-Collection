def test_strategy_with_a_lot_of_arrivals():
    """
    When the containers all have *a lot* of arrivals, and should thus be
    considered full, they should show up in the routing decisions.
    """
    pass


def test_strategy_considers_container_capacities():
    """
    Tests that the same number of arrivals does not mean the same for
    containers of different capacities: the capacity is taken into account by
    the strategy.
    """
    pass


def test_strategy_considers_container_arrival_rates():
    """
    In addition to container capacities, the strategy also takes into account
    the different average arrival rates at each container.
    """
    pass
