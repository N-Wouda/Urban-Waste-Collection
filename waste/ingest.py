import glob
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def make_tables(con: sqlite3.Connection):
    sql = """
        CREATE TABLE containers (
            container VARCHAR,
            cluster VARCHAR,
            capacity INT,
            latitude FLOAT,
            longitude FLOAT
        );

        CREATE TABLE arrivals (
            container VARCHAR,
            date DATE,
            successful BOOLEAN
        );

        CREATE TABLE services (
            container VARCHAR,
            date DATE
        );
    """

    con.executescript(sql)


def insert_containers(con: sqlite3.Connection, containers: pd.DataFrame):
    values = [
        (c.Container, c.ClusterName, c.PitCapacity, c.Latitude, c.Longitude)
        for _, c in containers.iterrows()
    ]

    con.executemany(
        """
            INSERT INTO containers (
                container,
                cluster,
                capacity,
                latitude,
                longitude
            ) VALUES (?, ?, ?, ?, ?);
        """,
        values,
    )

    con.commit()


def insert_arrivals(con: sqlite3.Connection, arrivals: pd.DataFrame):
    values = [
        (
            d.DumpLocationNr,
            datetime.strptime(d.RegMoment, "%d-%m-%Y %H:%M"),
            int(d.Successful) == 1,
        )
        for _, d in arrivals.iterrows()
    ]

    con.executemany(
        """
            INSERT INTO arrivals (
                container,
                date,
                successful
            ) VALUES (?, ?, ?);
        """,
        values,
    )

    con.commit()


def insert_services(con: sqlite3.Connection, services: pd.DataFrame):
    values = [
        (d.DumpLocationName, datetime.strptime(d.DATETIME, "%d-%m-%Y %H:%M"))
        for _, d in services.iterrows()
    ]

    con.executemany(
        """
            INSERT INTO services (
                container,
                date
            ) VALUES (?, ?);
        """,
        values,
    )

    con.commit()


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

        # Arrivals ("stortingen")
        for where in glob.iglob("data/Overzicht stortingen*.csv"):
            logger.info(f"Inserting arrivals from '{where}'.")
            arrivals = pd.read_csv(where, sep=";", dtype=object)
            insert_arrivals(con, arrivals)

        # Servicing ("ledigingen")
        logger.info("Inserting services.")
        where = "data/Overzicht ledigingen Q1 2023.csv"
        services = pd.read_csv(where, sep=";")
        services = services[services.FractionName == "RST"]  # only residential
        insert_services(con, services)


if __name__ == "__main__":
    main()
