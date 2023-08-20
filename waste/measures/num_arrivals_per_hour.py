import sqlite3

import numpy as np

from waste.constants import HOURS_IN_DAY


def num_arrivals_per_hour(con: sqlite3.Connection) -> list[float]:
    """
    Number of arrivals at each hour of the day, over all containers.
    This is helpful to quickly check that our arrival process is OK.
    """
    sql = """-- sql
        SELECT CAST(strftime('%H', time) AS INT) AS hour,
               COUNT(*)                          AS num_arrivals
        FROM arrival_events
        GROUP BY hour
        ORDER BY hour;
    """
    histogram = np.zeros((HOURS_IN_DAY,))
    for hour, num_arrivals in con.execute(sql):
        histogram[hour] = num_arrivals

    return histogram
