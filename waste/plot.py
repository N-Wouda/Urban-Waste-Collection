import argparse
from collections import defaultdict
from datetime import date, datetime, time
from itertools import cycle

import folium
import pandas as pd

from waste.classes import Database

# The commented colors are (too) hard to read on screen
colors = cycle(
    [
        #    'lightgreen',
        #    'lightblue',
        "darkblue",
        #    'darkpurple',
        # "beige",
        "darkgreen",
        "orange",
        "green",
        #    'lightred',
        "red",
        "black",
        # "gray",
        "pink",
        "blue",
        # "white",
        "purple",
        "cadetblue",
        #    'lightgray',
        "darkred",
    ]
)


def parse_args():
    parser = argparse.ArgumentParser(prog="plot_routes")
    parser.add_argument(
        "--start",
        required=True,
        type=date.fromisoformat,
        help="Start date in ISO format, e.g. 2023-08-10.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=date.fromisoformat,
        help="Finish date in ISO format, e.g. 2023-08-11 (inclusive).",
    )

    parser.add_argument("src_db", help="Location of the source database.")
    parser.add_argument("res_db", help="Location of the results database.")
    parser.add_argument("fig_name", help="Filename of figure.")

    return parser.parse_args()


def service_event_locations(
    start: datetime, end: datetime, db: Database
) -> pd.DataFrame:
    """
    Coordinates and routes of service event between start and end.
    """
    sql = """--sql
        SELECT se.*, l.latitude, l.longitude
        FROM service_events se
        JOIN containers c
            ON c.name = se.container
        JOIN locations l
            ON c.id_location = l.id_location
        WHERE se.time >= ? AND se.time <= ?
        ORDER BY se.id_route, se.time ASC;
    """
    return pd.read_sql_query(sql, db.write, params=(start, end))


def main():
    args = parse_args()

    src_db = args.src_db
    res_db = args.res_db
    fig_name = args.fig_name
    start = datetime.combine(args.start, time.min)
    end = datetime.combine(args.end, time.max)

    db = Database(src_db, res_db, exists_ok=True)
    df = db.compute(lambda db: service_event_locations(start, end, db))

    # A route is a list of services. Since we don't know the number of services
    # upfront, we use a defaultdict list to append the services
    routes = defaultdict(list)
    for _, row in df.iterrows():
        routes[row["id_route"]].append(row)

    center = [df["latitude"].mean(), df["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=13)

    for id_route, route in routes.items():
        depot_loc = db.depot().location
        locs = [(c["latitude"], c["longitude"]) for c in route]

        folium.PolyLine(
            locations=[loc for loc in [depot_loc, *locs, depot_loc]],
            tooltip=f"Route ID: {id_route}",
            color=next(colors),
        ).add_to(fmap)

        for service in route:
            folium.CircleMarker(
                location=(service["latitude"], service["longitude"]),
                tooltip=(
                    f"Container ID: {service['container']}<br>"
                    f"Time: {service['time']}"
                ),
                radius=8,
                weight=5,
            ).add_to(fmap)

    fmap.save(fig_name)


if __name__ == "__main__":
    main()
