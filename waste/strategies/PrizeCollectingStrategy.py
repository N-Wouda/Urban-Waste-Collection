from waste.classes import Route, ShiftPlanEvent, Simulator


class PrizeCollectingStrategy:
    """
    Dispatching via prize-collecting.
    """

    def __call__(self, sim: Simulator, event: ShiftPlanEvent) -> list[Route]:
        # TODO
        return []
