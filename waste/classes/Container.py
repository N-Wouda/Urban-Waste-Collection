from numpy.random import poisson, uniform

from waste.constants import HOURS_IN_DAY, VOLUME_RANGE

from .Event import Event, EventType


class Container:
    """
    Models an underground container. This container registers arrivals and
    services, and maintains the currently used volume and number of arrivals
    since last service.
    """

    def __init__(self, name: str, rates: list[float], capacity: float):
        assert len(rates) == HOURS_IN_DAY

        self.name = name
        self.rates = rates  # arrival rates, per clock hour ([0 - 23])
        self.capacity = capacity  # in volume, liters

        self.num_arrivals = 0  # number of arrivals since last service
        self.volume = 0.0  # current volume in container, in liters

    def arrivals_until(self, until: int) -> list[Event]:
        """
        Returns arrivals (events) for the period [0, until], where until is
        assumed to be in hours.
        """
        events = []

        for hour in range(until):
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this container.
            rate = self.rates[hour % len(self.rates)]
            num_arrivals = poisson(rate)

            volumes = uniform(*VOLUME_RANGE, size=num_arrivals)  # in liters
            arrivals = hour + uniform(size=num_arrivals)

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
        self.num_arrivals += 1
        self.volume += event.kwargs["volume"]

    def service(self):
        """
        Services this container.
        """
        self.num_arrivals = 0
        self.volume = 0.0

    def __str__(self) -> str:
        return (
            "Container("
            f"name={self.name}, "
            f"num_arrivals={self.num_arrivals}, "
            f"capacity={self.capacity}"
            ")"
        )

    # TODO
