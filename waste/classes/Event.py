from waste.enums import EventType


class Event:
    """
    Event class. Events have a time at which they are fired, and a type. The
    type determines the additional kwargs present.
    """

    def __init__(self, time: float, type: EventType, **kwargs):
        self.time = time
        self.type = type
        self.kwargs = kwargs

    def __str__(self) -> str:
        return (
            "Event("
            f"time={self.time:.2f}, "
            f"type={self.type.name}, "
            f"{len(self.kwargs)} kwargs"
            ")"
        )
