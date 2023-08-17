import argparse
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time

import folium
import pandas as pd

from waste.classes import Database

# The commented colors are (too) hard to read on screen
colors = [
    #    'lightgreen',
    #    'lightblue',
    "darkblue",
    #    'darkpurple',
    "beige",
    "darkgreen",
    "orange",
    "green",
    #    'lightred',
    "red",
    "black",
    "gray",
    "pink",
    "blue",
    "white",
    "purple",
    "cadetblue",
    #    'lightgray',
    "darkred",
]


@dataclass
class Service:
    location: tuple[float, float]
    container: str
    time: datetime


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
    start, end, con: sqlite3.Connection
) -> pd.DataFrame:
    """
    Coordinates and routes of service event between start and end.
    """
    sql = """ --sql
        SELECT se.*, l.latitude, l.longitude
        FROM service_events se, containers c
        JOIN locations l ON c.id_location = l.id_location
        AND c.name = se.container
        WHERE se.time >= ? AND se.time <= ?;
    """
    return pd.read_sql_query(sql, con, params=(start, end))


def main():
    args = parse_args()

    src_db = args.src_db
    res_db = args.res_db
    fig_name = args.fig_name
    start = datetime.combine(args.start, time.min)
    end = datetime.combine(args.end, time.max)

    db = Database(src_db, res_db, exists_ok=True)
    df = db.compute(lambda con: service_event_locations(start, end, con))

    # A route is a list of services. Since we don't know the number of services
    # upfront, we use a defaultdict list to append the services
    routes = defaultdict(list)
    for _, row in df.iterrows():
        id_route = row["id_route"]
        service = Service(
            (row["latitude"], row["longitude"]),
            row["container"],
            datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S"),
        )
        routes[id_route].append(service)

    center = [df["latitude"].mean(), df["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=13)

    # Plot route
    for id_route, route in routes.items():
        locations = [s.location for s in route]
        color = colors[id_route % len(colors)]
        folium.PolyLine(
            locations=locations,
            tooltip=f"Route ID: {id_route}",
            color=color,
        ).add_to(fmap)

    # plot service locations
    for id_route, route in routes.items():
        for service in route:
            folium.Marker(
                location=service.location,
                tooltip=(
                    f"Container ID: {service.container}<br>"
                    f"Time: {service.time:%d-%b:%H:%M}"
                ),
            ).add_to(fmap)

    fmap.save(fig_name)


if __name__ == "__main__":
    main()
