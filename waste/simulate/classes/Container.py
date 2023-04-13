from .Event import Event


class Container:
    rates: list[float]  # arrival rates, per clock hour ([0 - 23])

    def arrivals_until(self, until: float) -> list[Event]:
        """
        Returns arrivals (events) for the period [0, until], where until is
        assumed to be in hours.
        """
        return []

    # TODO
