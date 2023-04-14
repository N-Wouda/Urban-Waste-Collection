from enum import Enum


class EventType(Enum):
    ARRIVAL = 0
    SERVICE = 1
    SHIFT_PLAN = 2


class Event:
    def __init__(self, time: float, type: EventType, **kwargs):
        self.time = time
        self.type = type
        self.kwargs = kwargs

    def __str__(self) -> str:
        return (
            "Event("
            f"t = {self.time:.2f}, "
            f"{self.type.name}, "
            f"{len(self.kwargs)} kwargs"
            ")"
        )
