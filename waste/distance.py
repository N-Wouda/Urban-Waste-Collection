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


def query(base_url: str, points: str, **query) -> tuple[list[int], list[int]]:
    url = f"{base_url}/table/v1/driving/{points}?{urlencode(query)}"
    response = urlopen(url)
    data = json.loads(response.read())

    if data["code"] != "Ok":
        msg = f"Expected status code 'Ok', got '{data['code']}'."
        logger.error(msg)
        raise ValueError(msg)

    # Round values to nearest integers. As distance is in meters and duration
    # in seconds, this won't have much of an impact on quality.
    distances = [round(max(dist, 0)) for dist in data["distances"][0]]
    durations = [round(max(dur, 0)) for dur in data["durations"][0]]
    return distances, durations


def main():
    args = parse_args()
    con = sqlite3.connect(args.database)

    sql = """-- sql
        CREATE TABLE distances (
            from_location INTEGER REFERENCES locations,
            to_location INTEGER REFERENCES locations,
            distance INT -- in meters
        );

        CREATE TABLE durations (
            from_location INTEGER REFERENCES locations,
            to_location INTEGER REFERENCES locations,
            duration INT -- in seconds
        );
    """
    con.executescript(sql)

    sql = """-- sql
        SELECT id_location, name, longitude, latitude
        FROM locations
        ORDER BY id_location;
    """
    data = [tuple(datum) for datum in con.execute(sql)]
    ids = [id_location for id_location, *_ in data]
    points = ";".join(f"{lon},{lat}" for *_, lon, lat in data)

    for idx, (id_location, name, *_) in enumerate(data):
        logging.info(f"[#{id_location:>4}] Computing routing data for {name}.")
        dists, durs = query(
            args.api_url,
            points,
            annotations="duration,distance",
            skip_waypoints="true",
            sources=idx,  # OSRM takes an index into the points list
        )

        con.execute("BEGIN TRANSACTION;")
        con.executemany(
            "INSERT INTO distances VALUES (?, ?, ?)",
            [(id_location, other, dist) for other, dist in zip(ids, dists)],
        )
        con.executemany(
            "INSERT INTO durations VALUES (?, ?, ?)",
            [(id_location, other, dur) for other, dur in zip(ids, durs)],
        )
        con.commit()


if __name__ == "__main__":
    main()
