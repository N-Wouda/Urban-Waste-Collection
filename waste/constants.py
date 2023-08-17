from datetime import time, timedelta

from waste.enums import LocationType

__doc__ = """
    This file contains constants that are useful to gather in one place.
    Some of these are related to the simulation implementation, while others
    describe fixed municipality processes.
"""

# Stadsbeheer; the junkyard is ~200m down the road from this location.
# TODO get depot from database; don't rely on this
DEPOT = (
    "Depot",  # name
    "Duinkerkenstraat 45",  # description
    53.197625,  # latitude
    6.6127883,  # longitude
    LocationType.DEPOT,
)

BUFFER_SIZE: int = 999
HOURS_IN_DAY: int = 24
SHIFT_DURATION: timedelta = timedelta(hours=8)
VOLUME_RANGE: tuple[float, float] = (30, 65)  # in liters
SHIFT_PLAN_TIME: time = time(hour=7)
BREAKS: list[tuple[time, time, timedelta]] = [
    # Coffee break starting between 10:00 and 10:15, lasting 15 minutes, and
    # a lunch break starting between 12:00 and 12:30, lasting 30 minutes.
    (time(hour=10), time(hour=10, minute=15), timedelta(minutes=15)),
    (time(hour=12), time(hour=12, minute=30), timedelta(minutes=30)),
]
TIME_PER_CONTAINER = timedelta(minutes=3)
