import sqlite3
from typing import Optional


def avg_service_level(con: sqlite3.Connection) -> Optional[float]:
    """
    This measure computes the service level of serviced containers.
    """
    sql = """-- sql
        SELECT AVG(se.volume < c.capacity)
        FROM service_events AS se
            INNER JOIN source.containers AS c
                ON se.container = c.container;
    """
    row = con.execute(sql).fetchone()
    return row[0]
