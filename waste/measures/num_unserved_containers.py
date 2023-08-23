from waste.classes import Database


def num_unserved_containers(db: Database) -> int:
    """
    Returns the number of containers that have never been serviced during
    the simulation run.
    """
    sql = """--sql
        SELECT COUNT(DISTINCT containers.name)
        FROM containers
            LEFT JOIN service_events AS se
                ON se.container = containers.name
        WHERE se.container ISNULL;
    """
    row = db.write.execute(sql).fetchone()
    return row[0]
