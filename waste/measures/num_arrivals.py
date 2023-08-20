import sqlite3


def num_arrivals(con: sqlite3.Connection) -> float:
    """
    Total number of arrivals during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM arrival_events;"
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
