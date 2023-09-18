from datetime import datetime

from waste.classes import Database


def avg_num_services(db: Database, after: datetime) -> int:
    """
    Average number of services per container during the entire simulation.
    """
    sql = """--sql
        SELECT AVG(num_services)
        FROM (
            SELECT COUNT(*) AS num_services
            FROM service_events
            WHERE time > ?
            GROUP BY service_events.container
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0
