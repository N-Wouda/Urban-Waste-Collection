import sqlite3


def avg_route_stops(con: sqlite3.Connection) -> float:
    """
    Computes the average number of stops along routes, excluding the depot.
    """
    sql = """-- sql
        SELECT AVG(num_stops)
        FROM (
            SELECT id_route, COUNT(*) AS num_stops
            FROM service_events
            GROUP BY id_route
        );
    """
    row = con.execute(sql).fetchone()
    return res if (res := row[0]) else 0.0
