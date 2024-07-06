import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from waste.classes import Database


def avg_route_duration(db: Database, after: datetime) -> timedelta:
    """
    Computes the average duration travelled along routes, including taking
    breaks, service time at clusters, and the arcs to and from the depot.
    """
    loc2idx = {c.name: idx for idx, c in enumerate(db.clusters(), 1)}
    loc2idx["Depot"] = 0

    mat = db.durations()
    dur = timedelta(seconds=0)

    for route in _routes_with_stops(db.write, after):
        stops = np.array([0, *[loc2idx[name] for name in route["plan"]], 0])
        dur += mat[stops[:-1], stops[1:]].sum().item()
        dur += timedelta(seconds=route["duration"])

    return dur / max(_num_routes(db.write, after), 1)


def _num_routes(con: sqlite3.Connection, after: datetime) -> int:
    """
    Returns the number of routes in the database.
    """
    sql = """--sql
        SELECT COUNT(*)
        FROM routes
        WHERE start_time > ?;
    """
    row = con.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0


def _routes_with_stops(
    con: sqlite3.Connection, after: datetime
) -> list[dict[str, Any]]:
    """
    Returns lists of stops, one list for each route. Includes returns to the
    depot for breaks.
    """
    sql = """--sql
        SELECT se.id_route, c.name, se.duration, se.time
        FROM service_events AS se
            INNER JOIN clusters AS c
                ON se.cluster = c.name
        WHERE time > ?
        UNION
        SELECT id_route, 'Depot', duration, time
        FROM break_events
        WHERE time > ?
        ORDER BY id_route, time;  
    """

    # Since we want to compute the overall route duration, we need to track
    # the stops (route plan), and the duration taken at each stop. The latter
    # is stored in seconds.
    grouped = defaultdict(lambda: dict(plan=[], duration=0.0))  # type: ignore
    for id_route, loc_name, duration, _ in con.execute(sql, [after, after]):
        grouped[id_route]["plan"].append(loc_name)  # type: ignore
        grouped[id_route]["duration"] += duration

    return [plan for plan in grouped.values()]
