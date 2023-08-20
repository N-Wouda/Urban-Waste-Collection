from waste.classes import Database


def num_arrivals(db: Database) -> int:
    """
    Total number of arrivals during the entire simulation.
    """
    sql = "SELECT COUNT(*) FROM arrival_events;"
    row = db.write.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0
