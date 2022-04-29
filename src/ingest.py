import glob
import sqlite3
import string
from datetime import datetime
from pathlib import Path

import pandas as pd


def make_tables(con: sqlite3.Connection):
    sql = """
        CREATE TABLE containers (
            container VARCHAR,
            cluster VARCHAR,
            capacity INT,
            factor FLOAT,
            latitude FLOAT,
            longitude FLOAT
        );

        CREATE TABLE dumps (
            container VARCHAR,
            date DATE,
            qty INT,
            commercial BOOLEAN
        );
    """

    con.executescript(sql)


def insert_containers(con: sqlite3.Connection, containers: pd.DataFrame):
    values = [(c.Container,
               c.ClusterName,
               c.PitCapacity,
               c.VolumeCorrectionFactor,
               c.Latitude,
               c.Longitude)
              for _, c in containers.iterrows()]

    con.executemany("""INSERT INTO containers (
                            container, 
                            cluster, 
                            capacity, 
                            factor, 
                            latitude, 
                            longitude
                        ) VALUES (?, ?, ?, ?, ?, ?)""",
                    values)


def insert_dumps(con: sqlite3.Connection, dumps: pd.DataFrame):
    values = [(d.Container,
               datetime.strptime(f"{d.Datum} {d.Tijd}", "%d-%m-%Y %H:%M:%S"),
               int(d.Artikel.strip(string.ascii_letters)),
               d.Wijkparkstorting.strip() != '')
              for _, d in dumps.iterrows()]

    con.executemany("""INSERT INTO dumps (
                            container, 
                            date, 
                            qty, 
                            commercial
                        ) VALUES (?, ?, ?, ?)""",
                    values)


def main():
    # Remove existing database, if any - ingest starts from scratch.
    db = Path("data/waste.db")
    db.unlink(missing_ok=True)

    # Set-up database connection and table structure.
    con = sqlite3.connect("data/waste.db")
    make_tables(con)

    # Import data from raw Excel files, starting with the container data.
    containers = pd.read_excel("data/Containers/Containergegevens.xlsx")
    insert_containers(con, containers)

    for dump_loc in glob.iglob("data/Stortingen/*.csv"):
        dumps = pd.read_csv(dump_loc, sep=";")
        insert_dumps(con, dumps)

    con.commit()


if __name__ == "__main__":
    main()
