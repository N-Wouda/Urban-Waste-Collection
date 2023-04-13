from scipy.stats import poisson, uniform

from .Event import Event, EventType


class Container:
    rates: list[float]  # arrival rates, per clock hour ([0 - 23])

    def arrivals_until(self, until: int) -> list[Event]:
        """
        Returns arrivals (events) for the period [0, until], where until is
        assumed to be in hours.
        """
        events = []

        for hour in range(until):
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this container.
            rate = self.rates[hour % 24]
            num_arrivals = poisson.rvs(rate)  # arrivals this hour

            events += [
                Event(arrival, EventType.ARRIVAL, container=self)
                for arrival in uniform.rvs(loc=hour, size=num_arrivals)
            ]

        return events

    # TODO
