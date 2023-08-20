import sqlite3


def avg_route_stops(con: sqlite3.Connection) -> float:
    """
    Computes the average number of stops along routes, excluding the depot.
    """
    sql = """-- sql
        SELECT AVG(num_stops)
        FROM (
            SELECT routes.id_route, COUNT(se.id_route) AS num_stops
            FROM routes
                LEFT JOIN service_events se 
                    ON se.id_route = routes.id_route
            GROUP BY routes.id_route
        );
    """
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
