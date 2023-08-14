import argparse
import logging
from datetime import date, datetime, time

import numpy as np
import pandas as pd

from waste.classes import Database, Simulator
from waste.classes.Event import ArrivalEvent, ShiftPlanEvent
from waste.constants import SHIFT_PLAN_TIME, VOLUME_RANGE
from waste.strategies import STRATEGIES

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="simulate")
    subparsers = parser.add_subparsers(dest="strategy")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--start",
        required=True,
        type=date.fromisoformat,
        help="Start date in ISO format, e.g., 2023-08-10.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=date.fromisoformat,
        help="Finish date in ISO format, e.g., 2023-08-11.",
    )

    # TODO flesh out the following strategies
    subparsers.add_parser("baseline")
    subparsers.add_parser("greedy")
    subparsers.add_parser("prize")

    random = subparsers.add_parser("random")
    random.add_argument(
        "--containers_per_route",
        required=True,
        type=int,
        default=20,
    )

    return parser.parse_args()


def main():
    args = parse_args()
    if args.strategy not in STRATEGIES.keys():
        raise ValueError(f"Strategy '{args.strategy}' not understood.")

    start = args.start
    end = args.end
    if start >= end:
        raise ValueError("Start date lies after finish date.")

    logger.info(f"Running simulation with arguments {vars(args)}.")

    # Set up simulation environment and data
    db = Database(args.src_db, args.res_db)
    sim = Simulator(
        np.random.default_rng(args.seed),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = STRATEGIES[args.strategy](**vars(args))

    # Simulate and store results. First we create initial events: these are all
    # arrival events, and shift planning times. The simulation starts with
    # those events and processes them, which may add new ones as well.

    events = []
    for container in db.containers():
        deposit_times = pd.date_range(start, end, freq="H").to_pydatetime()
        volumes = sim.generator.uniform(
            low=VOLUME_RANGE[0], high=VOLUME_RANGE[1], size=len(deposit_times)
        )
        for t, volume in zip(deposit_times, volumes):
            events.append(ArrivalEvent(t, container=container, volume=volume))

    first_shift = datetime.combine(start, time(SHIFT_PLAN_TIME, 0, 0))
    for t in pd.date_range(first_shift, end, freq="24H").to_pydatetime():
        events.append(ShiftPlanEvent(t))

    sim(db.store, strategy, events)


if __name__ == "__main__":
    main()
