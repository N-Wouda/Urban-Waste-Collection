from dataclasses import dataclass
from datetime import time, timedelta


@dataclass
class Configuration:
    BREAKS: tuple[tuple[time, timedelta], ...] = (
        # Coffee break starting at 10:00 and lasting 30 minutes, and
        # a lunch break starting at 12:00, lasting 30 minutes.
        (time(hour=10), timedelta(minutes=30)),
        (time(hour=12), timedelta(minutes=30)),
    )
    SHIFT_DURATION: timedelta = timedelta(hours=6)  # excl. breaks
    SHIFT_PLAN_TIME: time = time(hour=7)  # noqa: RUF009
    VOLUME_RANGE: tuple[float, float, float] = (10, 30, 60)  # in liters

    # Time per cluster is the basic set-up and teardown needed at each cluster.
    # This is irrespective of the number of containers in a cluster. Then, the
    # time per container is the additional time needed to process each
    # container in a cluster. Thus, a cluster with three containers has a total
    # handling time of TIME_PER_CLUSTER + 3 * TIME_PER_CONTAINER.
    TIME_PER_CLUSTER: timedelta = timedelta(minutes=2)
    TIME_PER_CONTAINER: timedelta = timedelta(minutes=1)
