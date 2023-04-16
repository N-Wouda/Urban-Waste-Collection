import argparse
import json
import logging
import sqlite3
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="distance")

    parser.add_argument("database")
    parser.add_argument("--api_url", default="http://localhost:5000")

    return parser.parse_args()


def main():
    args = parse_args()

    with sqlite3.connect(args.database) as con:
        sql = """-- sql
            SELECT container, latitude, longitude
            FROM containers
            ORDER BY container;
        """
        data = [tuple(datum) for datum in con.execute(sql)]

    points = ";".join(f"{lat},{lon}" for _, lat, lon in data)
    base_params = dict(annotations="duration,distance", skip_waypoints="true")

    for idx, (name, *_) in enumerate(data):
        logging.info(f"[#{idx:>4}] Computing distances for {name}.")

        query = urlencode(base_params | dict(sources=idx))
        response = urlopen(f"{args.api_url}/table/v1/driving/{points}?{query}")

        if response.status != 200:
            msg = f"Could not compute distances for {name}."
            logger.error(msg)
            raise ValueError(msg)

        data = json.loads(response.read())

        if data["code"] != "Ok":
            msg = f"Expected status code 'Ok', got '{data['code']}'."
            logger.error(msg)
            raise ValueError(msg)

        distances = data["distances"]  # noqa
        durations = data["durations"]  # noqa

        # TODO


if __name__ == "__main__":
    main()
