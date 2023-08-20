import sqlite3


def num_services(con: sqlite3.Connection) -> float:
    """
    Total number of services during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM service_events;"
    row = con.execute(sql).fetchone()
    return res if (res := row[0]) else 0.0
