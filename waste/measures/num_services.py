import sqlite3


def num_services(con: sqlite3.Connection) -> float:
    """
    Total number of services during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM service_events;"
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
