from datetime import datetime

from waste.classes import Database


def avg_excess_volume(db: Database, after: datetime) -> float:
    """
    Computes the average excess volume: the average excess volume in clusters
    that overflowed. This is typically the part that can be found outside the
    clusters, on the street (so we would like it to be very small).
    """
    sql = """--sql
        SELECT AVG(se.volume - c.capacity)
        FROM service_events AS se
            INNER JOIN source.clusters AS c
                ON se.cluster = c.name
        WHERE se.volume > c.capacity AND se.time > ?;   
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
