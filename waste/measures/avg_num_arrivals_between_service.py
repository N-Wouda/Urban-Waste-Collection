from datetime import datetime

from waste.classes import Database


def avg_num_arrivals_between_service(db: Database, after: datetime) -> float:
    """
    Computes the average number of arrivals between services at the containers.
    """
    sql = """--sql
        SELECT AVG(num_arrivals)
        FROM service_events
        WHERE time > ?;
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
