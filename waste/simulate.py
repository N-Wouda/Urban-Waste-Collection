import logging.config

import tomli

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.toml", "rb") as file:
    logging.config.dictConfig(tomli.load(file))

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
        "--num_vehicles",
        type=int,
        help="Number of available vehicles. All if not defined.",
    )
    parser.add_argument(
        "--perfect_information",
        action="store_true",
        help="Whether the exact fill-rate of the clusters is known or not.",
    )
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

    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--deposit_volume", type=float, required=True)
    baseline.add_argument("--num_clusters", type=int, required=True)
    baseline.add_argument("--max_runtime", type=float, required=True)

    prize = subparsers.add_parser("prize")
    prize.add_argument("--rho", type=float, required=True)
    prize.add_argument("--max_runtime", type=float, required=True)
    prize.add_argument("--required_threshold", type=float, required=True)

    random = subparsers.add_parser("random")
    random.add_argument("--clusters_per_route", type=int, required=True)

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

    # Set up simulation environment and data. The number of actually available
    # vehicles can be limited via a command-line argument - a bit of a hack
    # that only works if all vehicles are identical (which is the case for our
    # data, but need not be true generally).
    db = Database(args.src_db, args.res_db)
    num_veh = args.num_vehicles if args.num_vehicles else len(db.vehicles())
    sim = Simulator(
        np.random.default_rng(args.seed),
        db.depot(),
        db.distances(),
        db.durations(),
        db.clusters(),
        db.vehicles()[:num_veh],
    )

    # Generate initial events *before* calling the strategy. This ensures we
    # have common random numbers for the arrivals, no matter what the strategy
    # does with the RNG.
    init_events = generate_events(sim, args.start, args.end, seed_events=True)
    strategy = STRATEGIES[args.strategy](sim, **vars(args))
    sim(db.store, strategy, init_events)


if __name__ == "__main__":
    main()
