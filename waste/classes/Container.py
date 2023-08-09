from typing import Iterator

from numpy.random import Generator

from waste.constants import HOURS_IN_DAY, VOLUME_RANGE

from .Event import ArrivalEvent


class Container:
    """
    Models an underground container. This container registers arrivals and
    services, and maintains the currently used volume and number of arrivals
    since last service.
    """

    def __init__(
        self,
        name: str,
        rates: list[float],
        capacity: float,
        location: tuple[float, float],
    ):
        assert len(rates) == HOURS_IN_DAY

        self.name = name
        self.rates = rates  # arrival rates, per clock hour ([0 - 23])
        self.capacity = capacity  # in volume, liters
        self.location = location  # (lat, lon) pair

        self.num_arrivals = 0  # number of arrivals since last service
        self.volume = 0.0  # current volume in container, in liters

    def arrivals_until(
        self,
        gen: Generator,
        until: int,
        volume_range: tuple[float, float] = VOLUME_RANGE,
    ) -> Iterator[ArrivalEvent]:
        """
        Returns arrivals (events) for the period [0, until], where until is
        assumed to be in hours. Each arrival event has a volume sampled
        uniformly from U[volume_range].
        """
        for hour in range(until):
            # Non-homogeneous Poisson arrivals, with hourly rates as given by
            # the rates list for this container.
            rate = self.rates[hour % len(self.rates)]
            num_arrivals = gen.poisson(rate)

            volumes = gen.uniform(*volume_range, size=num_arrivals)  # liters
            arrivals = hour + gen.uniform(size=num_arrivals)

            for arrival, volume in zip(arrivals, volumes):
                yield ArrivalEvent(
                    arrival,
                    container=self,
                    volume=volume,
                )

    def arrive(self, volume: float):
        """
        Registers an arrival at this container.
        """
        self.num_arrivals += 1
        self.volume += volume

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
