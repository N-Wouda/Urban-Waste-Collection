from datetime import datetime, timedelta
from typing import Iterator

import numpy as np


def equal_intervals(
    from_time: datetime, until_time: datetime, interval: timedelta
) -> Iterator[datetime]:
    current_time = from_time
    while current_time < until_time:
        yield current_time
        current_time += interval


def nhpp(
    rates: list[int], from_time: datetime, until_time: datetime
) -> Iterator[datetime]:
    """non homogeneous Poisson process. Rates are specified per hour.
    Rates must be in num/hour."""
    if len(rates) != 24:
        raise ValueError("The rates are not specified for all 24 hours.")

    rng = np.random.default_rng(12345)
    current_time = from_time
    while current_time < until_time:
        yield current_time
        lambda_t = rates[current_time.hour]
        time_to_next_event = rng.exponential(1 / lambda_t)
        current_time += timedelta(hours=time_to_next_event)


def main():
    from_time = datetime(2023, 8, 9, 10, 0)
    until_time = datetime(2023, 8, 9, 12, 0)

    for time in equal_intervals(
        from_time, until_time, interval=timedelta(minutes=12)
    ):
        print(time.strftime("%Y-%m-%d %H:%M:%S"))

    rates = [10] * 24

    for time in nhpp(rates, from_time, until_time):
        print(time.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
