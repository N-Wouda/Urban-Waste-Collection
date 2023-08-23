from datetime import datetime

from waste.classes import Database


def num_arrivals(db: Database, after: datetime) -> int:
    """
    Total number of arrivals during the entire simulation.
    """
    sql = """--sql
        SELECT COUNT(*)
        FROM arrival_events
        WHERE time > ?;
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0
