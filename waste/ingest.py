import glob
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def make_tables(con: sqlite3.Connection):
    sql = """-- sql
        CREATE TABLE containers (
            container VARCHAR,
            street VARCHAR,
            city VARCHAR,
            capacity INT,
            latitude FLOAT,
            longitude FLOAT
        );

        CREATE TABLE vehicles (
            vehicle VARCHAR,
            capacity INT
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


def insert_containers(con: sqlite3.Connection, containers: pd.DataFrame):
    values = [
        (
            r.DumpLocationName,
            r.Street,
            r.City,
            1000 * r.PitCapacity,  # in liters
            r.Latitude,
            r.Longitude,
        )
        for _, r in containers.iterrows()
    ]

    cols = ["container", "street", "city", "capacity", "latitude", "longitude"]
    df = pd.DataFrame(columns=cols, data=values)
    df.to_sql("containers", con, index=False, if_exists="append")


def insert_vehicles(con: sqlite3.Connection, vehicles: pd.DataFrame):
    values = [(r.Naam, r.Capaciteit) for _, r in vehicles.iterrows()]
    df = pd.DataFrame(columns=["vehicle", "capacity"], data=values)
    df.to_sql("vehicles", con, index=False, if_exists="append")


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
    # Remove existing database, if any - ingest starts from scratch.
    db = Path("data/waste.db")
    db.unlink(missing_ok=True)

    with sqlite3.connect("data/waste.db") as con:
        # Set-up database connection and table structure.
        logger.info("Creating tables.")
        make_tables(con)

        # Container data
        logger.info("Inserting containers.")
        containers = pd.read_excel("data/Containergegevens.xlsx")
        insert_containers(con, containers)

        # Vehicle data
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
