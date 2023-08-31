from datetime import time


class Vehicle:
    def __init__(
        self,
        name: str,
        capacity: float,
        shift_start: time = time.min,
        shift_end: time = time.max,
    ):
        self.name = name
        self.capacity = capacity
        self.shift_start = shift_start
        self.shift_end = shift_end

    def __str__(self) -> str:
        return (
            f"Vehicle({self.name=}, {self.capacity=:.2f}, "
            f"{self.shift_start=}, {self.shift_end=})"
        )
