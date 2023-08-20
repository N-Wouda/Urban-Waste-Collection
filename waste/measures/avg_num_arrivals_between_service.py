from waste.classes import Database


def avg_num_arrivals_between_service(db: Database) -> float:
    """
    Computes the average number of arrivals between services at the containers.
    """
    sql = "SELECT AVG(num_arrivals) FROM service_events;"
    row = db.write.execute(sql).fetchone()
    return row[0] if row[0] is not None else 0.0
