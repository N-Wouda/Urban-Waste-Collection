__doc__ = """
    This file contains constants that are useful to gather in one place.
    Some of these are related to the simulation implementation, while others
    describe fixed municipality processes.
"""

BUFFER_SIZE: int = 999
HOURS_IN_DAY: int = 24
VOLUME_RANGE: tuple[float, float] = (30, 65)  # in liters
SHIFT_PLANNING_HOURS: list[float] = [6, 12]
SERVICE_TIME_PER_CONTAINER: float = 180  # in seconds; three minutes
