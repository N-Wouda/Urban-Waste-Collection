from datetime import datetime, timedelta

import numpy as np

from waste.classes import ServiceEvent, Simulator
from waste.strategies import Strategy


def seed_strategy(sim: Simulator, strategy: Strategy):
    """
    Seeds the given strategy with some initial arrival and service events.
    TODO
    """
    for c in sim.containers:
        for num_arrivals in np.arange(start=1, stop=152, step=10):
            event = ServiceEvent(
                time=datetime.min,
                duration=timedelta(hours=0),
                id_route=0,
                container=c,
                vehicle=sim.vehicles[0],
            )

            event.seal()

            vol = sim.generator.uniform(*sim.config.VOLUME_RANGE, num_arrivals)
            event._num_arrivals = num_arrivals  # noqa: SLF001
            event._volume = sum(vol)  # noqa: SLF001

            strategy.observe(event)
