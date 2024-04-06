from datetime import time

from waste.constants import HOURS_IN_DAY


class Container:
    """
    Models a cluster of underground containers. This cluster registers arrivals
    and services, and tracks the currently used volume and number of arrivals
    since last service.
    """

    def __init__(
        self,
        name: str,
        id_location: int,
        rates: list[float],
        capacity: float,
        location: tuple[float, float],
        tw_late: time = time.max,
        num_containers: int = 1,
        correction_factor: float = 1.0,
    ):
        assert len(rates) == HOURS_IN_DAY

        self.name = name
        self.id_location = id_location
        self.rates = rates  # arrival rates, per clock hour ([0 - 23])
        self.capacity = capacity  # in volume, liters
        self.correction_factor = correction_factor  # cap. correction factor
        self.location = location  # (lat, lon) pair
        self.tw_late = tw_late
        self.num_containers = num_containers  # number of containers in cluster

        self.num_arrivals = 0  # number of arrivals since last service
        self.volume = 0.0  # current volume in container, in liters

    @property
    def corrected_capacity(self) -> float:
        """
        Capacity of this container with the municipality's correction factor
        applied.
        """
        return self.correction_factor * self.capacity

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
