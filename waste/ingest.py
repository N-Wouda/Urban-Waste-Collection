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

        CREATE TABLE containers (
            name VARCHAR UNIQUE,
            cluster VARCHAR,
            container VARCHAR,
            id_location INT REFERENCES locations,
            capacity FLOAT
        );

        CREATE TABLE vehicles (
            name VARCHAR UNIQUE,
            capacity FLOAT
        );

        CREATE TABLE arrivals (
            container VARCHAR,
            date DATE,
            successful BOOLEAN
        );

        CREATE TABLE container_rates (
            container VARCHAR,
            hour INT,
            rate FLOAT
        );

        CREATE TABLE services (
            container VARCHAR,
            date DATE
        );
    """

    con.executescript(sql)


def insert_locations(con: sqlite3.Connection, containers: pd.DataFrame):
    values = [DEPOT]
    values += [
        (
            r.ClusterCode + "-" + r.ContainerCode,
            r.ClusterOmschrijving,
            float(r.Latitude),
            float(r.Longitude),
            LocationType.CONTAINER,
        )
        for _, r in containers.iterrows()
    ]

    columns = ["name", "description", "latitude", "longitude", "type"]
    df = pd.DataFrame(columns=columns, data=values)
    df.to_sql("locations", con, index_label="id_location", if_exists="replace")


def insert_containers(con: sqlite3.Connection, containers: pd.DataFrame):
    sql = "SELECT name, id_location FROM locations;"
    name2loc = {name: id_location for name, id_location in con.execute(sql)}
    values = [
        (
            r.DumpLocationName,
            r.ClusterCode,
            r.ContainerCode,
            name2loc[r.ClusterCode + "-" + r.ContainerCode],
            1000 * float(r.PitCapacity),  # capacity in liters
        )
        for _, r in containers.iterrows()
    ]

    columns = ["name", "cluster", "container", "id_location", "capacity"]
    df = pd.DataFrame(columns=columns, data=values)
    df.to_sql("containers", con, index=False, if_exists="replace")


def insert_vehicles(con: sqlite3.Connection, vehicles: pd.DataFrame):
    values = [(r.Naam, 1000 * r.Capaciteit) for _, r in vehicles.iterrows()]
    df = pd.DataFrame(columns=["name", "capacity"], data=values)
    df.to_sql("vehicles", con, index=False, if_exists="replace")


def insert_arrivals(con: sqlite3.Connection, arrivals: pd.DataFrame):
    values = [
        (
            r.DumpLocationNr,
            datetime.strptime(r.RegMoment, "%d-%m-%Y %H:%M"),
            int(r.Successful) == 1,
        )
        for _, r in arrivals.iterrows()
    ]

    df = pd.DataFrame(columns=["container", "date", "successful"], data=values)
    df.to_sql("arrivals", con, index=False, if_exists="append")


def insert_arrival_rates(con: sqlite3.Connection):
    sql = "SELECT JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) FROM arrivals;"
    horizon = con.execute(sql).fetchone()

    sql = """-- sql
        INSERT INTO container_rates
        SELECT *
        FROM (
            SELECT container,
                   STRFTIME('%H', date) AS hour,
                   COUNT(date) / ? AS rate
            FROM arrivals
            WHERE container NOTNULL
            GROUP BY container, hour
        );
    """
    con.execute(sql, horizon)
    con.commit()


def insert_services(con: sqlite3.Connection, services: pd.DataFrame):
    values = [
        (r.DumpLocationName, datetime.strptime(r.DATETIME, "%d-%m-%Y %H:%M"))
        for _, r in services.iterrows()
    ]

    df = pd.DataFrame(columns=["container", "date"], data=values)
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

    # Depot and container data. Here we apply some trickery: there's a public
    # list of containers that we want, and an internal list Stadsbeheer has
    # provided for us. The latter contains a lot more places and data. The
    # places we do not need (those are not part of the collection process), but
    # the additional data is very useful.
    logger.info("Inserting depot and containers.")

    public = pd.read_csv("data/Containerlocaties.csv", dtype="str")
    internal = pd.read_excel("data/Containergegevens.xlsx", dtype="str")
    public["code"] = public.ClusterCode + "-" + public.ContainerCode
    internal["code"] = internal.ClusterName + "-" + internal.Container
    containers = public.merge(internal, on="code")

    insert_locations(con, containers)
    insert_containers(con, containers)

    # Vehicle data.
    logger.info("Inserting vehicles.")
    vehicles = pd.read_csv("data/Voertuigen.csv", sep=";")
    insert_vehicles(con, vehicles)

    # Arrivals ("stortingen")
    for where in glob.iglob("data/Overzicht stortingen*.csv"):
        logger.info(f"Inserting arrivals from '{where}'.")
        arrivals = pd.read_csv(where, sep=";", dtype=object)
        insert_arrivals(con, arrivals)

    # Pre-compute hourly arrival rates for each container, based on the
    # current arrivals table.
    logger.info("Inserting hourly arrival rates.")
    insert_arrival_rates(con)

    # Servicing ("ledigingen")
    logger.info("Inserting services.")
    where = "data/Overzicht ledigingen Q1 2023.csv"
    services = pd.read_csv(where, sep=";")
    services = services[services.FractionName == "RST"]  # only residential
    insert_services(con, services)


if __name__ == "__main__":
    main()
