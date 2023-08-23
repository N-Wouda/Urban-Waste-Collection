from datetime import time

from waste.constants import HOURS_IN_DAY


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
        tw_late: time = time.max,
    ):
        assert len(rates) == HOURS_IN_DAY

        self.name = name
        self.rates = rates  # arrival rates, per clock hour ([0 - 23])
        self.capacity = capacity  # in volume, liters
        self.location = location  # (lat, lon) pair
        self.tw_late = tw_late

        self.num_arrivals = 0  # number of arrivals since last service
        self.volume = 0.0  # current volume in container, in liters

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
