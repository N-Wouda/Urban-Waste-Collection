from datetime import datetime

from waste.classes import Database


def avg_num_routes_per_day(db: Database, after: datetime) -> float:
    """
    This measure computes the average number of routes needed to visit the
    scheduled containers each day.
    """
    sql = """--sql
        SELECT AVG(num_routes)
        FROM (
            SELECT strftime('%Y-%m-%d', start_time) AS date,
                   COUNT(*)                         AS num_routes
            FROM routes
            WHERE start_time > ?
            GROUP BY date
            ORDER BY date
        );
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0] if row[0] is not None else 0.0
