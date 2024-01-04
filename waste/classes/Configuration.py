from dataclasses import dataclass
from datetime import time, timedelta


@dataclass
class Configuration:
    BREAKS: tuple[tuple[time, timedelta], ...] = (
        # Coffee break starting at 10:00 and lasting 30 minutes, and
        # a lunch break starting at 12:00, also lasting 30 minutes.
        (time(hour=10), timedelta(minutes=30)),
        (time(hour=12), timedelta(minutes=30)),
    )
    SHIFT_DURATION: timedelta = timedelta(hours=6)  # excl. breaks
    SHIFT_PLAN_TIME: time = time(hour=7)  # noqa: RUF009
    TIME_PER_CONTAINER: timedelta = timedelta(minutes=3, seconds=30)
    VOLUME_RANGE: tuple[float, float] = (10, 60)  # in liters
