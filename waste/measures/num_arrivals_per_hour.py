from datetime import datetime

from waste.classes import Database
from waste.constants import HOURS_IN_DAY


def num_arrivals_per_hour(db: Database, after: datetime) -> list[int]:
    """
    Number of arrivals at each hour of the day, over all containers.
    This is helpful to quickly check that our arrival process is OK.
    """
    sql = """-- sql
        SELECT CAST(strftime('%H', time) AS INT) AS hour,
               COUNT(*)                          AS num_arrivals
        FROM arrival_events
        WHERE time > ?
        GROUP BY hour
        ORDER BY hour;
    """
    histogram = [0] * HOURS_IN_DAY
    for hour, num_arrivals in db.write.execute(sql, [after]):
        histogram[hour] = num_arrivals

    return histogram
