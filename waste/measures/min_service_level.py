from datetime import datetime

from waste.classes import Database


def min_service_level(db: Database, after: datetime) -> float:
    """
    This measure computes the worst service level of any serviced cluster, that
    is, the minimum average service level over all serviced clusters.
    """
    sql = """-- sql
        SELECT MIN(service_level)
        FROM (
            SELECT AVG(se.volume <= c.capacity) AS service_level
            FROM service_events AS se
                INNER JOIN source.clusters AS c
                    ON se.cluster = c.name
            WHERE se.time > ?
            GROUP BY c.name
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 1.0
