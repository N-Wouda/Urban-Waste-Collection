from datetime import datetime

from waste.classes import Database


def min_service_level(db: Database, after: datetime) -> float:
    """
    This measure computes the service level of worst container, that is,
    the minimum average service level over all serviced containers.
    """
    sql = """-- sql
        SELECT MIN(service_level)
        FROM (
            SELECT AVG(se.volume <= c.capacity) AS service_level
            FROM service_events AS se
                INNER JOIN source.containers AS c
                    ON se.container = c.name
            WHERE se.time > ?
            GROUP BY c.name
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 1.0
