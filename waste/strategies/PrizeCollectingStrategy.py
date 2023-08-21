from waste.classes import Event, Route, ShiftPlanEvent, Simulator


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
        # TODO
        pass
