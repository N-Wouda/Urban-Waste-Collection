import sqlite3
from collections import defaultdict

import numpy as np

from waste.classes import Database


def avg_route_distance(db: Database) -> float:
    """
    Computes the average distance (in meters) travelled along routes, including
    breaks and the arcs to and from the depot.
    """
    mat = db.distances()
    dist = 0

    for plan in _stops(db.write):
        stops = np.array([0, *plan, 0])
        dist += mat[stops[:-1], stops[1:]].sum()

    return dist / max(_num_routes(db.write), 1)


def _num_routes(con: sqlite3.Connection) -> int:
    """
    Returns the number of routes in the database.
    """
    sql = "SELECT COUNT(*) FROM routes;"
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0


def _stops(con: sqlite3.Connection) -> list[list[int]]:
    """
    Returns lists of stops, one list for each route. Includes breaks.
    """
    sql = """--sql
        SELECT se.id_route, c.id_location, se.time
        FROM service_events AS se
            INNER JOIN containers AS c
                ON se.container = c.name
        UNION
        SELECT id_route, :depot, time
        FROM break_events
        ORDER BY id_route, time;  
    """
    stops = con.execute(sql, dict(depot=0)).fetchall()

    grouped = defaultdict(list)
    for id_route, id_location, _ in stops:
        grouped[id_route].append(id_location)

    return [plan for plan in grouped.values()]
