from waste.classes import Event, Route, ServiceEvent, ShiftPlanEvent, Simulator


class PrizeCollectingStrategy:
    """
    Dispatching via prize-collecting.
    """

    def __init__(self, **kwargs):
        pass

    def plan(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # TODO
        return []

    def observe(self, event: Event):
        if not isinstance(event, ServiceEvent):
            # We're only interested in service events, since those tell us
            # something about whether a container has overflowed.
            return

        # container = event.container
        # num_arrivals = event.num_arrivals
        # has_overflow = event.volume > container.capacity

        # TODO update parameter estimate for container
