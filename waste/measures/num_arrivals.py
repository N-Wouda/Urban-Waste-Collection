import sqlite3


def num_arrivals(con: sqlite3.Connection) -> float:
    """
    Total number of arrivals during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM arrival_events;"
    row = con.execute(sql).fetchone()
    return res if (res := row[0]) else 0.0
