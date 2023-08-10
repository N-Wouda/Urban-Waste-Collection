import argparse
import logging
from datetime import datetime, timedelta

import numpy as np

from waste.arrivals import equal_intervals
from waste.classes import Database, Simulator
from waste.classes.Event import ShiftPlanEvent
from waste.constants import SHIFT_PLAN_TIME, VOLUME_RANGE
from waste.strategies import STRATEGIES

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="simulate")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")

    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start datetime, e.g., 2023-08-10T07:00",
    )
    parser.add_argument(
        "--finish",
        type=str,
        required=True,
        help="Finish datetime, e.g., 2023-08-10T07:00",
    )

    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--strategy", choices=STRATEGIES.keys(), required=True)

    return parser.parse_args()


def main():
    args = parse_args()

    from_time = datetime.strptime(args.start, "%Y-%m-%dT%H:%M")
    until_time = datetime.strptime(args.finish, "%Y-%m-%dT%H:%M")
    if from_time >= until_time:
        raise ValueError("Start date lies after finish date.")

    logger.info(f"Running simulation with arguments {vars(args)}.")

    generator = np.random.default_rng(args.seed)

    # Set up simulation environment and data
    db = Database(args.src_db, args.res_db)
    sim = Simulator(
        generator,
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = STRATEGIES[args.strategy]()

    # Simulate and store results. First we create initial events: these are all
    # arrival events, and shift planning times. The simulation starts with
    # those events and processes them, which may add new ones as well.
    events = []
    for container in db.containers():
        deposits = list(
            equal_intervals(from_time, until_time, timedelta(days=1))
        )
        volumes = generator.uniform(
            low=VOLUME_RANGE[0], high=VOLUME_RANGE[1], size=len(deposits)
        )
        for deposit in container.deposits(deposits, volumes):
            events.append(deposit)

    first_shift = from_time.replace(hour=SHIFT_PLAN_TIME)
    if first_shift < from_time:
        first_shift += timedelta(days=1)
    for time in equal_intervals(first_shift, until_time, timedelta(days=1)):
        events.append(ShiftPlanEvent(time))

    sim(db.store, strategy, events, from_time, until_time)


if __name__ == "__main__":
    main()
