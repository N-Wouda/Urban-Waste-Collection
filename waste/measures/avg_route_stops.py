from datetime import datetime

from waste.classes import Database


def avg_route_stops(db: Database, after: datetime) -> float:
    """
    Computes the average number of stops along routes, excluding the depot
    and breaks.
    """
    sql = """-- sql
        SELECT AVG(num_stops)
        FROM (
            SELECT routes.id_route, 
                   SUM(IFNULL(c.num_containers, 0)) AS num_stops
            FROM routes
                LEFT JOIN service_events se 
                    ON se.id_route = routes.id_route
                LEFT JOIN clusters c
                    ON c.name = se.cluster
            WHERE routes.start_time > ?
            GROUP BY routes.id_route
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
