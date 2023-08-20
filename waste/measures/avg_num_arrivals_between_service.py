import sqlite3


def avg_num_arrivals_between_service(con: sqlite3.Connection) -> float:
    """
    Computes the average number of arrivals between services at the containers.
    """
    sql = "SELECT AVG(num_arrivals) FROM service_events;"
    row = con.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
