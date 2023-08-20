import argparse
import json

from waste.classes import Database
from waste.measures import MEASURES


def parse_args():
    parser = argparse.ArgumentParser(prog="analyze")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")
    parser.add_argument("--output", help="Output file (should be JSON).")

    return parser.parse_args()


def main():
    args = parse_args()
    db = Database(args.src_db, args.res_db, exists_ok=True)

    values = {}
    for func in MEASURES:
        name = func.__name__
        val = db.compute(func)
        values[name] = val
        print(f"{name:36}: {val}")

    if args.output:
        with open(args.output, "w+") as fh:
            json.dump(values, fh, default=str)


if __name__ == "__main__":
    main()
