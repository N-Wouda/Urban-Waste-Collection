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


def query(
    base_url: str,
    points: str,
    source: int,
) -> tuple[list[float], list[float]]:
    params = dict(
        annotations="duration,distance",
        skip_waypoints="true",
        sources=source,
    )

    url = f"{base_url}/table/v1/driving/{points}?{urlencode(params)}"
    response = urlopen(url)

    if response.status != 200:
        msg = f"Could not compute distances for source {source}."
        logger.error(msg)
        raise ValueError(msg)

    data = json.loads(response.read())

    if data["code"] != "Ok":
        msg = f"Expected status code 'Ok', got '{data['code']}'."
        logger.error(msg)
        raise ValueError(msg)

    # Only return the first value since we have only one source.
    return data["distances"][0], data["durations"][0]


def main():
    args = parse_args()

    with sqlite3.connect(args.database) as con:
        sql = """-- sql
            CREATE TABLE distances (
                a VARCHAR,
                b VARCHAR,
                distance FLOAT -- in meters
            );

            CREATE TABLE durations (
                a VARCHAR,
                b VARCHAR,
                duration FLOAT -- in seconds
            )
        """
        con.executescript(sql)

        sql = """-- sql
            SELECT container, longitude, latitude
            FROM containers
            ORDER BY container;
        """
        data = [tuple(datum) for datum in con.execute(sql)]
        names = [name for name, *_ in data]
        points = ";".join(f"{lon},{lat}" for _, lon, lat in data)

        for idx, (name, *_) in enumerate(data):
            logging.info(f"[#{idx:>4}] Computing routing data for {name}.")
            distances, durations = query(args.api_url, points, idx)

            con.execute("BEGIN TRANSACTION;")
            con.executemany(
                "INSERT INTO distances VALUES (?, ?, ?)",
                [(name, other, dist) for other, dist in zip(names, distances)],
            )
            con.executemany(
                "INSERT INTO durations VALUES (?, ?, ?)",
                [(name, other, dur) for other, dur in zip(names, durations)],
            )
            con.commit()


if __name__ == "__main__":
    main()
