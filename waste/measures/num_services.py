from datetime import datetime

from waste.classes import Database


def num_services(db: Database, after: datetime) -> int:
    """
    Total number of services during the entire simulation.
    """
    sql = """--sql
        SELECT COUNT(*)
        FROM service_events
        WHERE time > ?;
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0
