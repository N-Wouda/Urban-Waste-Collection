import logging.config

import tomli

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.toml", "rb") as file:
    logging.config.dictConfig(tomli.load(file))

import argparse
import glob
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from waste.constants import DEPOT
from waste.enums import LocationType

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="ingest")

    parser.add_argument("database")

    return parser.parse_args()


def make_tables(con: sqlite3.Connection):
    sql = """-- sql
        CREATE TABLE locations (
            id_location INT PRIMARY KEY,
            name varchar UNIQUE,
            description VARCHAR,
            latitude FLOAT,
            longitude FLOAT,
            type INT  -- see LocationType enum
        );

        CREATE TABLE clusters (
            name VARCHAR UNIQUE,
            id_location INT REFERENCES locations,
            tw_late TIME CHECK(tw_late IS strftime('%H:%M:%S', tw_late)),
            num_containers INT,
            capacity FLOAT,
            correction_factor FLOAT
        );

        CREATE TABLE vehicles (
            name VARCHAR UNIQUE,
            capacity FLOAT
        );

        CREATE TABLE arrivals (
            cluster VARCHAR REFERENCES clusters(name),
            date DATE,
            successful BOOLEAN
        );

        CREATE TABLE cluster_rates (
            cluster VARCHAR REFERENCES clusters(name),
            hour INT,
            rate FLOAT
        );

        CREATE TABLE services (
            cluster VARCHAR REFERENCES clusters(name),
            date DATE
        );
    """

    con.executescript(sql)


def insert_locations(con: sqlite3.Connection, containers: pd.DataFrame):
    clusters = containers.drop_duplicates(subset=["ClusterCode"])

    values = [DEPOT]
    values += [
        (
            r.ClusterCode,
            r.ClusterOmschrijving,
            float(r.Latitude),
            float(r.Longitude),
            LocationType.CLUSTER,
        )
        for _, r in clusters.iterrows()
    ]

    columns = ["name", "description", "latitude", "longitude", "type"]
    df = pd.DataFrame(columns=columns, data=values)
    df.to_sql("locations", con, index_label="id_location", if_exists="replace")


def insert_container_clusters(
    con: sqlite3.Connection, containers: pd.DataFrame
):
    sql = "SELECT name, id_location FROM locations;"
    name2loc = {name: id_location for name, id_location in con.execute(sql)}

    containers["PitCapacity"] = containers.PitCapacity.astype(float)
    containers[
        "VolumeCorrectionFactor"
    ] = containers.VolumeCorrectionFactor.astype(float)

    # We actually insert clusters of containers, that is, the total group at
    # a given location. Typically a cluster consists of one or more actual
    # containers, but since they are serviced together they basically act as
    # a single, large container, and we model it in that fashion.
    cols = [
        "City",
        "Container",
        "PitCapacity",
        "VolumeCorrectionFactor",
        "ClusterCode",
    ]
    clusters = (
        containers[cols]
        .groupby(containers.ClusterCode)
        .agg(
            {
                "City": "first",
                "Container": "count",
                "PitCapacity": "sum",
                "VolumeCorrectionFactor": "mean",
                "ClusterCode": "first",
            }
        )
    )

    values = [
        (
            r.ClusterCode,
            name2loc[r.ClusterCode],
            # Time windows only apply to clusters in the inner city (in Dutch
            # "Binnenstad").
            "11:00:00" if "Binnenstad" in r.City else "23:59:59",
            r.Container,  # number of containers in this cluster
            1000 * r.PitCapacity,  # capacity in liters
            r.VolumeCorrectionFactor,  # correction to capacity
        )
        for _, r in clusters.iterrows()
    ]

    columns = [
        "name",
        "id_location",
        "tw_late",
        "num_containers",
        "capacity",
        "correction_factor",
    ]
    df = pd.DataFrame(columns=columns, data=values)
    df.to_sql("clusters", con, index=False, if_exists="replace")


def insert_vehicles(con: sqlite3.Connection, vehicles: pd.DataFrame):
    values = [(r.Naam, 1000 * r.Capaciteit) for _, r in vehicles.iterrows()]
    df = pd.DataFrame(columns=["name", "capacity"], data=values)
    df.to_sql("vehicles", con, index=False, if_exists="replace")


def insert_arrivals(
    con: sqlite3.Connection,
    containers: pd.DataFrame,
    arrivals: pd.DataFrame,
):
    con2cluster = {
        str(r.DumpLocationName).strip(): r.ClusterCode
        for _, r in containers.iterrows()
    }

    values = [
        (
            # Some arrivals are not matched with a container cluster in our
            # data set. That can happen - the arrival data also contains
            # contract containers outside the municipality that are not handled
            # via the daily urban waste system. Manual checks suggest those
            # account for less than 2% of all arrivals, so this should be OK.
            con2cluster.get(r.DumpLocationNr.strip()),
            datetime.strptime(r.RegMoment, "%d-%m-%Y %H:%M"),
            int(r.Successful) == 1,
        )
        for _, r in arrivals[~pd.isna(arrivals.DumpLocationNr)].iterrows()
    ]

    df = pd.DataFrame(columns=["cluster", "date", "successful"], data=values)
    df.to_sql("arrivals", con, index=False, if_exists="append")


def insert_arrival_rates(con: sqlite3.Connection):
    sql = "SELECT JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) FROM arrivals;"
    horizon = con.execute(sql).fetchone()

    sql = """-- sql
        INSERT INTO cluster_rates
        SELECT *
        FROM (
            SELECT cluster,
                   STRFTIME('%H', date) AS hour,
                   COUNT(date) / ? AS rate
            FROM arrivals
            WHERE cluster NOTNULL
            GROUP BY cluster, hour
        );
    """
    con.execute(sql, horizon)
    con.commit()


def insert_services(
    con: sqlite3.Connection,
    containers: pd.DataFrame,
    services: pd.DataFrame,
):
    con2cluster = {
        r.DumpLocationName.strip(): r.ClusterCode
        for _, r in containers.iterrows()
    }

    values = [
        (
            # As with arrivals, some services cannot be matched with containers
            # in our data set because the service data contains more container
            # locations - including quite a few not involved in daily waste
            # collection.
            con2cluster.get(r.DumpLocationName.strip()),
            datetime.strptime(r.DATETIME, "%d-%m-%Y %H:%M"),
        )
        for _, r in services.iterrows()
    ]

    df = pd.DataFrame(columns=["cluster", "date"], data=values)
    df.to_sql("services", con, index=False, if_exists="append")


def main():
    args = parse_args()

    # Remove existing database, if any - ingest starts from scratch.
    db = Path(args.database)
    db.unlink(missing_ok=True)

    con = sqlite3.connect(args.database)

    # Set-up database connection and table structure.
    logger.info("Creating tables.")
    make_tables(con)

    # Depot and cluster data. Here we apply some trickery: there's a public
    # list of containers that we want, and an internal list Stadsbeheer has
    # provided for us. The latter contains a lot more places and data. We do
    # not need the places (those are not part of the collection process), but
    # the additional data is very useful.
    logger.info("Inserting depot and container clusters.")

    public = pd.read_csv("data/Containerlocaties.csv", dtype="str")
    internal = pd.read_excel("data/Containergegevens.xlsx", dtype="str")
    public["code"] = public.ClusterCode + "-" + public.ContainerCode
    internal["code"] = internal.ClusterName + "-" + internal.Container
    containers = public.merge(internal, on="code")

    insert_locations(con, containers)
    insert_container_clusters(con, containers)

    # Vehicle data.
    logger.info("Inserting vehicles.")
    vehicles = pd.read_csv("data/Voertuigen.csv", sep=";")
    insert_vehicles(con, vehicles)

    # Arrivals ("stortingen")
    for where in glob.iglob("data/Overzicht stortingen*.csv"):
        logger.info(f"Inserting arrivals from '{where}'.")
        arrivals = pd.read_csv(where, sep=";", dtype="str")
        insert_arrivals(con, containers, arrivals)

    # Pre-compute hourly arrival rates for each container, based on the
    # current arrivals table.
    logger.info("Inserting hourly arrival rates.")
    insert_arrival_rates(con)

    # Servicing ("ledigingen")
    logger.info("Inserting services.")
    where = "data/Overzicht ledigingen Q1 2023.csv"
    services = pd.read_csv(where, sep=";", dtype="str")
    services = services[services.FractionName == "RST"]  # only residential
    insert_services(con, containers, services)


if __name__ == "__main__":
    main()
