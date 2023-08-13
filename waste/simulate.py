import argparse
import logging
from datetime import datetime

import numpy as np
import pandas as pd

from waste.classes import Database, Simulator
from waste.classes.Event import ShiftPlanEvent
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
        "--from_time",
        required=True,
        type=datetime.fromisoformat,
        help="Start datetime in ISO format, e.g., 2023-08-10T07:00.",
    )
    parser.add_argument(
        "--until_time",
        required=True,
        type=datetime.fromisoformat,
        help="Finish datetime in ISO format, e.g., 2023-08-10T07:00.",
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

    generator = np.random.default_rng(3)
    from_time = args.from_time
    until_time = args.until_time
    if from_time >= until_time:
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
    # deposit_times = pd.date_range(from_time, until_time, freq="H").to_
    # print(deposit_times)
    # quit()

    events = []
    for container in db.containers():
        deposit_times = pd.date_range(
            from_time, until_time, freq="H"
        ).to_pydatetime()
        volumes = generator.uniform(
            low=VOLUME_RANGE[0], high=VOLUME_RANGE[1], size=len(deposit_times)
        )
        for deposit in container.deposits(deposit_times, volumes):
            events.append(deposit)
    # for event in events:
    #     print(event.time, type(event.time))
    #     quit()

    first_shift = from_time.replace(hour=SHIFT_PLAN_TIME)
    shiftplan_times = pd.date_range(
        first_shift, until_time, freq="24H"
    ).to_pydatetime()
    for time in shiftplan_times:
        events.append(ShiftPlanEvent(time))

    sim(db.store, strategy, events, from_time, until_time)


if __name__ == "__main__":
    main()
