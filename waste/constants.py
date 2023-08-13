from waste.enums import LocationType

__doc__ = """
    This file contains constants that are useful to gather in one place.
    Some of these are related to the simulation implementation, while others
    describe fixed municipality processes.
"""

# Stadsbeheer; the junkyard is ~200m down the road from this location.
DEPOT = (
    "Depot",  # name
    "Duinkerkenstraat 45",  # description
    53.197625,  # latitude
    6.6127883,  # longitude
    LocationType.DEPOT,
)

BUFFER_SIZE: int = 999
HOURS_IN_DAY: int = 24
VOLUME_RANGE: tuple[float, float] = (30, 65)  # in liters
SHIFT_PLAN_TIME: float = 7  # 7 in the morning
BREAKS: list[tuple[float, float, float]] = [
    (3, 3.25, 0.25),  # coffee break: 15min, around 10 (three hours into shift)
    (5, 5.5, 0.5),  # lunch break: 30min, around 12 (five hours into shift)
]
TIME_PER_CONTAINER: float = 180 / 3600  # in hours; three minutes
