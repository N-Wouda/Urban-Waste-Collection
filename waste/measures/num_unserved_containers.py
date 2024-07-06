from datetime import datetime

from waste.classes import Database


def num_unserved_containers(db: Database, after: datetime) -> int:
    """
    Returns the number of container clusters that have never been serviced
    during the simulation run.
    """
    sql = """--sql
        SELECT COUNT(DISTINCT clusters.name)
        FROM clusters
            LEFT JOIN service_events AS se
                ON se.cluster = clusters.name AND se.time > ?
        WHERE se.cluster ISNULL;
    """
    row = db.write.execute(sql, [after]).fetchone()
    return row[0]
