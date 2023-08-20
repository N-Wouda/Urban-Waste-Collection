import sqlite3


def avg_route_distance(con: sqlite3.Connection) -> float:
    """
    Computes the average distance (in meters) travelled along routes including
    from/to the depot.
    """
    # TODO verify that this is indeed correct.
    sql = """-- sql
        SELECT AVG(to_dist.distance + from_depot.distance)
        FROM (
            SELECT id_route,
                   loc.id_location,  -- if null then from/to depot
                   IFNULL(loc_prev.id_location, :depot) AS prev_location,
                   IFNULL(loc_next.id_location, :depot) AS next_location
            FROM (
                SELECT id_route,
                       container,
                       LAG(container) OVER (PARTITION BY id_route)  AS prev,
                       LEAD(container) OVER (PARTITION BY id_route) AS next
                FROM service_events
            )
            INNER JOIN source.locations AS loc ON loc.name = container
            LEFT JOIN source.locations AS loc_prev ON loc_prev.name = prev
            LEFT JOIN source.locations AS loc_next ON loc_next.name = next
        )
        -- This join gets us all distances to the next stop, including the
        -- final return to the depot at the end of the route.
        INNER JOIN source.distances AS to_dist
            ON (
                to_dist.from_location = id_location
                AND to_dist.to_location = next_location
            )
        -- This join gets us the distance from the depot to the first stop.
        INNER JOIN source.distances AS from_depot
            ON (
                from_depot.from_location = prev_location
                AND from_depot.to_location = id_location
                AND prev_location = :depot
            );
    """
    row = con.execute(sql, dict(depot=0)).fetchone()
    return row[0] if row[0] is not None else 0.0
