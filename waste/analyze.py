import argparse

from waste.classes import Database
from waste.measures import MEASURES


def parse_args():
    parser = argparse.ArgumentParser(prog="analyze")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")

    return parser.parse_args()


def main():
    args = parse_args()
    db = Database(args.src_db, args.res_db, exists_ok=True)

    # Compute performance measures from stored data.
    for name, func in MEASURES.items():
        print(f"{name:30}: {db.compute(func)}")


if __name__ == "__main__":
    main()
