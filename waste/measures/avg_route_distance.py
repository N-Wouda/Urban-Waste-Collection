import sqlite3
from collections import defaultdict
from datetime import datetime

import numpy as np

from waste.classes import Database


def avg_route_distance(db: Database, after: datetime) -> float:
    """
    Computes the average distance (in meters) travelled along routes, including
    breaks and the arcs to and from the depot.
    """
    loc2idx = {c.name: idx for idx, c in enumerate(db.containers(), 1)}
    loc2idx["Depot"] = 0

    mat = db.distances()
    dist = 0

    for plan in _stops(db.write, after):
        stops = np.array([0, *[loc2idx[name] for name in plan], 0])
        dist += mat[stops[:-1], stops[1:]].sum()

    return dist / max(_num_routes(db.write, after), 1)


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


def _stops(con: sqlite3.Connection, after: datetime) -> list[list[str]]:
    """
    Returns lists of stops, one list for each route. Includes returns to the
    depot for breaks.
    """
    sql = """--sql
        SELECT se.id_route, c.name, se.time
        FROM service_events AS se
            INNER JOIN containers AS c
                ON se.container = c.name
        WHERE time > ?
        UNION
        SELECT id_route, 'Depot', time
        FROM break_events
        WHERE time > ?
        ORDER BY id_route, time;  
    """

    grouped = defaultdict(list)
    for id_route, loc_name, _ in con.execute(sql, [after, after]):
        grouped[id_route].append(loc_name)

    return [plan for plan in grouped.values()]
