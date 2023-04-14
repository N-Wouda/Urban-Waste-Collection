from numpy.random import poisson, uniform

from .Event import Event, EventType


class Container:
    def __init__(self, name: str, rates: list[float], capacity: float):
        assert len(rates) == 24

        self.name = name
        self.rates = rates  # arrival rates, per clock hour ([0 - 23])
        self.capacity = capacity  # in volume, liters

        self.deposits = 0  # number of arrivals since last service
        self._volume = 0.0  # current volume in container, in liters

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
            num_arrivals = poisson(rate)
            arrivals = hour + uniform(size=num_arrivals)

            # TODO parametrise 30 and 65
            volumes = uniform(low=30, high=65, size=num_arrivals)

            events += [
                Event(
                    arrival,
                    EventType.ARRIVAL,
                    container=self,
                    volume=volume,
                )
                for arrival, volume in zip(arrivals, volumes)
            ]

        return events

    def arrive(self, event: Event):
        """
        Registers an arrival at this container.
        """
        self.deposits += 1
        self._volume += event.kwargs["volume"]

    def service(self):
        """
        Services this container.
        """
        self.deposits = 0
        self._volume = 0.0

    def __str__(self) -> str:
        return (
            "Container("
            f"name={self.name}, "
            f"deposits={self.deposits}, "
            f"capacity={self.capacity}"
            ")"
        )

    # TODO
