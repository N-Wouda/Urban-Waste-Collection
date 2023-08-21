from collections import defaultdict

import numpy as np
from sklearn.linear_model import SGDClassifier

from waste.classes import Event, Route, ServiceEvent, ShiftPlanEvent, Simulator


class PrizeCollectingStrategy:
    """
    Dispatching via prize-collecting.
    """

    def __init__(self, sim: Simulator, rho: int, threshold: float, **kwargs):
        self.sim = sim
        self.rho = rho
        self.threshold = threshold

        self.data: dict[int, list[tuple[int, bool]]] = defaultdict(list)
        self.models: list[SGDClassifier] = []

        for _ in sim.containers:
            model = SGDClassifier(
                loss="log_loss",
                penalty=None,
                fit_intercept=False,
            )

            model.fit([0, 100], [0, 1])  # TODO make this data an argument
            self.models.append(model)

    def plan(self, event: ShiftPlanEvent) -> list[Route]:
        # Step 1. Update the models with data observed since the last shift
        # plan, and clear the data.
        for idx, container in enumerate(self.sim.containers):
            data = np.array(self.data[id(container)])
            self.models[idx].partial_fit(data[0, :], data[1, :])
            self.data[id(container)] = []

        # Step 2. Determine prizes, required containers, and solve the VRP.
        # probs = [
        #     m.predict_proba(c.num_arrivals)
        #     for c, m in zip(self.sim.containers, self.models)
        # ]

        # prizes = [int(self.rho * prob) for prob in probs]
        # required = [prob > self.threshold for prob in probs]

        # TODO

        # Step 3. Return the route plan.
        # TODO
        return []

    def observe(self, event: Event):
        if isinstance(event, ServiceEvent):
            # Store the new data. We will update the model in one batch the
            # next time we plan a shift.
            container = event.container
            num_arrivals = event.num_arrivals
            has_overflow = event.volume > container.capacity
            self.data[id(container)].append((num_arrivals, has_overflow))
