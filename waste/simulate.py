import argparse
import logging
from datetime import date

import numpy as np

from waste.classes import Database, Simulator
from waste.functions import generate_events
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
        help="Start date in ISO format, e.g. 2023-08-10.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=date.fromisoformat,
        help="Finish date in ISO format, e.g. 2023-08-11 (inclusive).",
    )

    # TODO flesh out the following strategies
    subparsers.add_parser("baseline")

    greedy = subparsers.add_parser("greedy")
    greedy.add_argument("--num_containers", type=int, default=20)
    greedy.add_argument("--max_runtime", type=float, default=5)

    subparsers.add_parser("prize")

    random = subparsers.add_parser("random")
    random.add_argument("--containers_per_route", type=int, default=20)

    return parser.parse_args()


def validate_args(args):
    if args.strategy not in STRATEGIES.keys():
        raise ValueError(f"Strategy '{args.strategy}' not understood.")

    if args.start >= args.end:
        raise ValueError("start >= end not understood.")


def main():
    args = parse_args()
    validate_args(args)

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
    events = generate_events(sim, args.start, args.end)
    sim(db.store, strategy, events)


if __name__ == "__main__":
    main()
