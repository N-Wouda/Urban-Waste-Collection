import argparse
import logging

import numpy as np

from waste.simulate import STRATEGIES, Database, Simulator

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="run")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")

    parser.add_argument(
        "--horizon",
        required=True,
        type=int,
        help="Time horizon for the simulation (in hours).",
    )
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--strategy", choices=STRATEGIES.keys(), required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    logger.info(f"Running simulation with arguments {vars(args)}.")

    np.random.seed(args.seed)

    # Set up simulation environment and data
    db = Database(args.src_db, args.res_db)

    containers = db.containers()
    vehicles = db.vehicles()

    # Simulate and store results
    sim = Simulator(containers, vehicles)
    res = sim(args.horizon, STRATEGIES[args.strategy])
    db.store(res)


if __name__ == "__main__":
    main()
