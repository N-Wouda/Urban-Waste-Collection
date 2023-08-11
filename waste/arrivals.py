import statistics
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


class NHPP:
    def __init__(
        self,
        start: datetime,
        rates: list[float],
        periods: list[timedelta],
        seed=3,
    ):
        """Return arrival times of a non-homogeneous Poisson process, starting
        from START.

        The RATES are piecewise constant on the
        PERIODS. The unit of rate is number per hour. A period is a time
        interval specified in hours. The rates are assumed to be
        cyclic: once we hit the end of PERIODS, we start again.
        """
        if len(rates) != len(periods):
            raise ValueError(
                "The length of the times and the rates are not the same."
            )

        self.rates = rates
        self.deltas = periods
        self.gen = np.random.default_rng(seed)

        # Down is the last time a rate change occured before time NOW.
        # Up is the next time a rate change will occure after time NOW.

        # Find the right starting period.
        self.down = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.period = 0
        self.up = self.down + self.deltas[self.period]
        while self.up < start:
            self.down = self.up
            self.period += 1
            self.up += self.deltas[self.period]

        # NOW is the arrival time
        self.now = self.down

    def __call__(self) -> datetime:
        x = timedelta(hours=self.gen.exponential())
        thres = x + self.rates[self.period] * (self.now - self.down)
        tot = self.rates[self.period] * (self.up - self.down)
        while tot < thres:
            self.down = self.up
            self.period = (self.period + 1) % len(self.rates)
            self.up += self.deltas[self.period]
            tot += self.rates[self.period] * (self.up - self.down)
        self.now = self.up - (tot - thres) / self.rates[self.period]
        return self.now


def main():
    from_time = datetime(2023, 8, 9, 10, 0)
    until_time = datetime(2023, 8, 9, 12, 0)

    for time in equal_intervals(
        from_time, until_time, interval=timedelta(minutes=12)
    ):
        print(time.strftime("%Y-%m-%d %H:%M:%S"))

    s = datetime(2023, 8, 9, 10, 0)
    finish = datetime(2023, 8, 19, 10, 0)
    rates = list(range(13))
    periods = [timedelta(hours=2)] * len(rates)
    nhpp = NHPP(s, rates, periods)

    num = 0
    while (t := nhpp()) < finish:
        num += 1

    total_hours = (t - s).total_seconds() // 3600
    expected_arrrivals = total_hours * statistics.mean(rates)
    print(expected_arrrivals, num)


if __name__ == "__main__":
    main()
