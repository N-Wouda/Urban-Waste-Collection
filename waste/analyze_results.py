import argparse
import sqlite3

from waste.measures import MEASURES


def parse_args():
    parser = argparse.ArgumentParser(prog="simulate")

    parser.add_argument("src_db", help="Location of the input database.")
    parser.add_argument("res_db", help="Location of the output database.")

    return parser.parse_args()


def main():
    args = parse_args()

    con = sqlite3.connect(args.res_db)
    con.execute("ATTACH DATABASE ? AS source;", (args.src_db,))

    # Compute performance measures from stored data
    res = {name: func(con) for name, func in MEASURES.items()}
    for k, v in res.items():
        print(f"{k:30} : {v}")


if __name__ == "__main__":
    main()
