from waste.classes import Database


def num_services(db: Database) -> int:
    """
    Total number of services during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM service_events;"
    row = db.write.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0
