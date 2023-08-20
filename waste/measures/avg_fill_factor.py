import sqlite3


def avg_fill_factor(con: sqlite3.Connection) -> float:
    """
    This measure computes the average fill factor of serviced containers.
    """
    sql = """-- sql
        SELECT AVG(se.volume / c.capacity)
        FROM service_events AS se
            INNER JOIN source.containers AS c
                ON se.container = c.name;
    """
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
