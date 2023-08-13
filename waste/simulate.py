import argparse
import logging
from datetime import datetime, timedelta

import numpy as np

from waste.arrivals import PeriodAdder
from waste.classes import Database, Simulator
from waste.classes.Event import ShiftPlanEvent
from waste.constants import SHIFT_PLAN_TIME, VOLUME_RANGE
from waste.strategies import STRATEGIES

logger = logging.getLogger(__name__)


def valid_datetime_format(arg_datetime):
    try:
        datetime.strptime(arg_datetime, "%Y-%m-%dT%H:%M")
        return arg_datetime
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Invalid datetime format. Please use: 'yyyy-mm-ddThh:mm'."
        )


def parse_args():
    parser = argparse.ArgumentParser(prog="simulate")
    subparsers = parser.add_subparsers(dest="strategy")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--start",
        type=valid_datetime_format,
        required=True,
        help="Start datetime, e.g., 2023-08-10T07:00",
    )

    parser.add_argument(
        "--finish",
        type=valid_datetime_format,
        required=True,
        help="Finish datetime, e.g., 2023-08-10T07:00",
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

    generator = np.random.default_rng(3)

    from_time = datetime.strptime(args.start, "%Y-%m-%dT%H:%M")
    until_time = datetime.strptime(args.finish, "%Y-%m-%dT%H:%M")
    if from_time >= until_time:
        raise ValueError("Start date lies after finish date.")

    logger.info(f"Running simulation with arguments {vars(args)}.")

    if args.strategy not in STRATEGIES.keys():
        raise ValueError(f"Strategy '{args.strategy}' not understood.")

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
        deposits = []
        gen = PeriodAdder(from_time, [timedelta(hours=1)])
        while (time := gen()) <= until_time:
            deposits.append(time)
        volumes = generator.uniform(
            low=VOLUME_RANGE[0], high=VOLUME_RANGE[1], size=len(deposits)
        )
        for deposit in container.deposits(deposits, volumes):
            events.append(deposit)

    # The first shift should start after from_time
    first_shift = from_time.replace(hour=SHIFT_PLAN_TIME)
    if first_shift < from_time:
        first_shift += timedelta(days=1)
    gen = PeriodAdder(from_time, [timedelta(days=1)])
    while (time := gen()) <= until_time:
        events.append(ShiftPlanEvent(time))

    sim(db.store, strategy, events, from_time, until_time)


if __name__ == "__main__":
    main()
