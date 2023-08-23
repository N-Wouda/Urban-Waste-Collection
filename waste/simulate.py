import logging.config

import tomli

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.toml", "rb") as file:
    logging.config.dictConfig(tomli.load(file))

import argparse
import logging
from datetime import date, datetime

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
    parser.add_argumemt(
        "--warmup_end",
        type=datetime.fromisoformat,
        default=datetime.min,
        help="End ISO datetime of the warmup period. Default no warmup.",
    )

    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--deposit_volume", type=float, required=True)
    baseline.add_argument("--num_containers", type=int, required=True)
    baseline.add_argument("--max_runtime", type=float, required=True)

    greedy = subparsers.add_parser("greedy")
    greedy.add_argument("--num_containers", type=int, required=True)
    greedy.add_argument("--max_runtime", type=float, required=True)

    prize = subparsers.add_parser("prize")
    prize.add_argument("--rho", type=float, required=True)
    prize.add_argument("--threshold", type=float, required=True)
    prize.add_argument("--deposit_volume", type=float, required=True)
    prize.add_argument("--max_runtime", type=float, required=True)

    random = subparsers.add_parser("random")
    random.add_argument("--containers_per_route", type=int, required=True)

    return parser.parse_args()


def validate_args(args):
    if args.strategy not in STRATEGIES:
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
        db.depot(),
        db.distances(),
        db.durations(),
        db.containers(),
        db.vehicles(),
    )

    strategy = STRATEGIES[args.strategy](sim, **vars(args))

    # Simulate and store results. First we create initial events: these are all
    # arrival events, and shift planning times. The simulation starts with
    # those events and processes them, which may add new ones as well.
    events = generate_events(sim, args.start, args.end)
    sim(db.store, strategy, events, store_after=args.warmup_end)


if __name__ == "__main__":
    main()
