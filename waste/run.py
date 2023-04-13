import argparse
import logging

from waste.simulate import STRATEGIES, Environment

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="run")

    parser.add_argument(
        "--horizon",
        required=True,
        type=float,
        help="Time horizon for the simulation (in hours).",
    )
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--strategy", choices=STRATEGIES.keys(), required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    logger.info(f"Running simulation with arguments {vars(args)}.")

    # Set up simulation environment
    containers = []  # TODO
    vehicles = []  # TODO
    env = Environment(containers, vehicles)

    # Simulate
    env.simulate(args.horizon, STRATEGIES[args.strategy])

    # Compute and store performance measures
    # TODO


if __name__ == "__main__":
    main()
