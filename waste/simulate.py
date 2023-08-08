import argparse
import logging

import numpy as np

from waste.classes import Database, Simulator
from waste.classes.Event import ShiftPlanEvent
from waste.constants import HOURS_IN_DAY, SHIFT_PLAN_TIME
from waste.strategies import STRATEGIES

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="simulate")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")

    parser.add_argument(
        "--horizon",
        required=True,
        type=int,
        help="Time horizon for the simulation (in hours).",
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--strategy", choices=STRATEGIES.keys(), required=True)
    parser.add_argument("--strategy_seed", type=int, required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    logger.info(f"Running simulation with arguments {vars(args)}.")

    np.random.seed(args.seed)

    # Set up simulation environment and data
    db = Database(args.src_db, args.res_db)
    sim = Simulator(
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    generator = np.random.default_rng(args.strategy_seed)
    strategy = STRATEGIES[args.strategy](generator)

    # Simulate and store results. First we create initial events: these are all
    # arrival events, and shift planning times. The simulation starts with
    # those events and processes them, which may add new ones as well.
    events = []
    for container in db.containers():
        for arrival in container.arrivals_until(args.horizon):
            events.push(arrival)

    for day in range(0, args.horizon, HOURS_IN_DAY):
        if day + SHIFT_PLAN_TIME <= args.horizon:
            events.push(ShiftPlanEvent(day + SHIFT_PLAN_TIME))

    sim(args.horizon, db.store, strategy, events)


if __name__ == "__main__":
    main()
