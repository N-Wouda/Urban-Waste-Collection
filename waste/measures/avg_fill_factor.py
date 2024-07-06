from datetime import datetime

from waste.classes import Database


def avg_fill_factor(db: Database, after: datetime) -> float:
    """
    This measure computes the average fill factor of serviced clusters.
    """
    sql = """-- sql
        SELECT AVG(se.volume / c.capacity)
        FROM service_events AS se
            INNER JOIN source.clusters AS c
                ON se.cluster = c.name
        WHERE se.time > ?;
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
