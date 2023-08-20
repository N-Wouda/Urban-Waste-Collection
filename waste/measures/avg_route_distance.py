from collections import defaultdict

from waste.classes import Database


def avg_route_distance(db: Database) -> float:
    """
    Computes the average distance (in meters) travelled along routes, including
    breaks and the arcs to and from the depot.
    """
    sql = """--sql
        SELECT se.id_route, c.id_location, se.time
        FROM service_events AS se
            INNER JOIN containers AS c
                ON se.container = c.name
        UNION
        SELECT id_route, :depot, time
        FROM break_events
        ORDER BY id_route, time;  
    """
    rows = db.write.execute(sql, dict(depot=0)).fetchall()
    grouped = defaultdict(list)

    for id_route, id_location, _ in rows:
        grouped[id_route].append(id_location)

    mat = db.distances()
    dist = 0
    for plan in grouped.values():
        stops = [0, *plan, 0]
        for idx, stop in enumerate(stops[1:], 1):
            dist += mat[stops[idx - 1], stop]

    return dist / max(len(grouped), 1)
