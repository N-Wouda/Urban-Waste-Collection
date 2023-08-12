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


class PeriodAdder:
    """Return arrival times seupared by PERIODS.

    Starting from START,  add cyclically the period lengths of PERIODS.
    """

    def __init__(self, start: datetime, periods: list[timedelta]):
        self.now = start
        self.periods = periods
        self.period = 0

    def __call__(self):
        self.now += self.periods[self.period]
        self.period = (self.period + 1) % len(self.periods)
        return self.now


class NHPP:
    """Return arrival times of a non-homogeneous Poisson process.

    Start from START. The RATES are piecewise constant on the PERIODS.
    The unit of rate is number per hour. The rates and periods  are used
    be cyclicly.
    """

    def __init__(
        self,
        start: datetime,
        rates: list[float],
        periods: list[timedelta],
        seed=3,
    ):
        if len(rates) != len(periods):
            raise ValueError(
                "The length of the times and the rates are not the same."
            )

        self.rates = rates
        self.deltas = periods
        self.gen = np.random.default_rng(seed)

        # self.now is the arrival time
        # self.down is the last time a rate change occured before NOW.
        # self.up is the next time a rate change will occure afte time NOW.

        # Find the right starting period.
        self.down = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.period = 0
        self.up = self.down + self.deltas[self.period]
        while self.up < start:
            self.down = self.up
            self.period += 1
            self.up += self.deltas[self.period]

        self.now = self.down

    def __call__(self) -> datetime:
        self.now += (
            timedelta(hours=self.gen.exponential()) / self.rates[self.period]
        )
        if self.now > self.up:
            thres = self.rates[self.period] * (self.now - self.down)
            tot = self.rates[self.period] * (self.up - self.down)
            while tot < thres:
                self.down = self.up
                self.period = (self.period + 1) % len(self.rates)
                self.up += self.deltas[self.period]
                tot += self.rates[self.period] * (self.up - self.down)
            self.now = self.up - (tot - thres) / self.rates[self.period]
        return self.now


def main():
    start = datetime(2023, 8, 9, 10, 0)
    finish = datetime(2023, 8, 9, 18, 0)
    periods = [timedelta(hours=1), timedelta(hours=2)]

    equal = PeriodAdder(start, periods)

    while (t := equal()) < finish:
        print(t)

    rates = list(range(13))
    periods = [timedelta(hours=2)] * len(rates)

    nhpp = NHPP(start, rates, periods)

    num = 0
    while (t := nhpp()) < finish:
        num += 1
        print(t)

    total_hours = (t - start).total_seconds() // 3600
    expected_arrrivals = total_hours * statistics.mean(rates)
    print(expected_arrrivals, num)


if __name__ == "__main__":
    main()
