from datetime import datetime

from waste.classes import Database


def avg_route_clusters(db: Database, after: datetime) -> float:
    """
    Computes the average number of container clusters along routes. While the
    number of stops (see ``avg_route_stops``) provides a similar measure, it
    counts every container as a unique stop. In practice, many containers are
    part of a cluster of containers, which might all be serviced at the same
    time.
    """
    sql = """-- sql
        SELECT AVG(num_clusters)
        FROM (
            SELECT routes.id_route, COUNT(se.id_route) AS num_clusters
            FROM routes
                LEFT JOIN service_events se 
                    ON se.id_route = routes.id_route
            WHERE routes.start_time > ?
            GROUP BY routes.id_route
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
