from datetime import time


class Vehicle:
    def __init__(
        self,
        name: str,
        capacity: float,
        shift_start: time = time.min,
        shift_end: time = time.max,
        num_available: int = 1,
    ):
        self.name = name
        self.capacity = capacity
        self.num_available = num_available
        self.shift_start = shift_start
        self.shift_end = shift_end

    def __str__(self) -> str:
        return f"Vehicle(name={self.name}, capacity={self.capacity:.2f})"

    # TODO
