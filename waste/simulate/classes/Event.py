from enum import IntEnum


class EventType(IntEnum):
    ARRIVAL = 0
    SERVICE = 1
    SHIFT_PLAN = 2


class Event:
    def __init__(self, time: float, type: EventType, **kwargs):
        self.time = time
        self.type = type
        self.kwargs = kwargs

    def __str__(self) -> str:
        return f"Event({self.time = }, {self.type = }, {self.kwargs = })"