from __future__ import annotations

import logging
import math
import sqlite3
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from waste.constants import BUFFER_SIZE, HOURS_IN_DAY, ID_DEPOT
from waste.enums import LocationType

from .Container import Container
from .Depot import Depot
from .Event import ArrivalEvent, Event, ServiceEvent
from .Route import Route
from .Vehicle import Vehicle

if TYPE_CHECKING:
    from waste.measures import Measure


logger = logging.getLogger(__name__)


class Database:
    """
    Simple database wrapper/model class for interacting with the static and
    simulation data.
    """

    def __new__(cls, src_db: str, res_db: str, exists_ok: bool = False):
        if Path(res_db).exists() and not exists_ok:
            raise FileExistsError(f"Database {res_db} already exists!")

        return super().__new__(cls)

    def __init__(self, src_db: str, res_db: str, exists_ok: bool = False):
        self.buffer: list[ArrivalEvent | ServiceEvent] = []
        self.read = sqlite3.connect(src_db)

        # Prepare the result database
        res_db_exists = Path(res_db).exists()
        self.write = sqlite3.connect(res_db)
        self.write.execute("ATTACH DATABASE ? AS source;", (src_db,))

        if not res_db_exists:
            self.write.executescript(
                """-- sql
                    CREATE TABLE arrival_events (
                        time FLOAT,
                        container VARCHAR,
                        volume FLOAT
                    );

                    CREATE TABLE routes (
                        id_route INTEGER PRIMARY KEY,
                        vehicle NAME
                    );

                    CREATE TABLE service_events (
                        time FLOAT,
                        container VARCHAR,
                        id_route INTEGER references routes,
                        num_arrivals INT,
                        volume FLOAT
                    );
                """
            )

    @cache
    def containers(self) -> list[Container]:
        sql = """-- sql
            SELECT cr.container,
                   c.capacity,
                   cr.hour,
                   cr.rate
            FROM container_rates AS cr
                    INNER JOIN containers AS c
                                ON c.name = cr.container
            ORDER BY c.id_location, cr.hour;  -- must order by ID, not name!
        """
        capacities: dict[str, float] = {}
        rates: dict[str, np.ndarray] = {}

        for name, capacity, hour, rate in self.read.execute(sql):
            if name not in rates:
                rates[name] = np.zeros(HOURS_IN_DAY)

            capacities[name] = capacity
            rates[name][hour] = rate

        sql = """-- sql
            SELECT c.name, l.latitude, l.longitude
            FROM containers AS c
                    INNER JOIN locations AS l
                            ON l.id_location = c.id_location;
        """
        name2loc = {name: loc for name, *loc in self.read.execute(sql)}

        return [
            Container(name, rates[name], capacity, name2loc[name])
            for name, capacity in capacities.items()
        ]

    @cache
    def depot(self) -> Depot:
        sql = "SELECT name, latitude, longitude FROM locations WHERE type = ?;"
        rows = [d for d in self.read.execute(sql, (LocationType.DEPOT,))]
        row = rows[0]
        assert len(rows) == 1  # there should be only a single depot!
        return Depot(name=row[0], location=row[1:])

    @cache
    def distances(self) -> np.array:
        """
        Returns the matrix of travel distances (in meters) for the depot (at
        index 0) and all containers returned by ``containers()``, in order.
        The distance matrix is *not* symmetric.
        """
        cursor = self.read.execute("SELECT distance FROM distances;")
        data = np.array([distance for distance in cursor])
        size = math.isqrt(len(data))
        distances = np.array(data).reshape((size, size))

        id_containers = _containers2loc(self.read, self.containers())
        id_locations = [ID_DEPOT, *id_containers]
        return distances[np.ix_(id_locations, id_locations)]

    @cache
    def durations(self) -> np.array:
        """
        Returns the matrix of travel durations (in seconds) for the depot (at
        index 0) and all containers returned by ``containers()``, in order.
        The duration matrix is *not* symmetric.
        """
        cursor = self.read.execute("SELECT duration FROM durations;")
        data = np.array([duration for duration in cursor])
        size = math.isqrt(len(data))
        durations = np.array(data).reshape((size, size))

        id_containers = _containers2loc(self.read, self.containers())
        id_locations = [ID_DEPOT, *id_containers]
        return durations[np.ix_(id_locations, id_locations)] / 3600  # in hours

    @cache
    def vehicles(self) -> list[Vehicle]:
        sql = "SELECT name, capacity FROM vehicles;"
        return [
            Vehicle(name, capacity)
            for name, capacity in self.read.execute(sql)
        ]

    def compute(self, measure: Measure) -> Any:
        """
        Computes the given performance measure on the simulation database
        connection. Ensures all buffered data is committed before the measure
        is computed.
        """
        self._commit()
        return measure(self.write)

    def store(self, item: Event | Route) -> Optional[int]:
        # Only arrival, service and route events are logged; other arguments
        #  are currently an intended no-op.
        match item:
            case (ArrivalEvent() | ServiceEvent()) as event:
                assert event.is_sealed()

                self.buffer.append(event)
                if len(self.buffer) >= BUFFER_SIZE:
                    self._commit()

                return None
            case Route(vehicle=vehicle):
                sql = "INSERT INTO routes (vehicle) VALUES (?)"
                cursor = self.write.execute(sql, (vehicle.name,))
                self.write.commit()
                return cursor.lastrowid
            case _:
                return None

    def _commit(self):
        self.write.execute("BEGIN TRANSACTION;")

        arrivals = [
            (
                event.time,
                event.container.name,
                event.volume,
            )
            for event in self.buffer
            if isinstance(event, ArrivalEvent)
        ]

        self.write.executemany(
            """-- sql
                INSERT INTO arrival_events (
                    time,
                    container,
                    volume
                ) VALUES (?, ?, ?)
            """,
            arrivals,
        )

        services = [
            (
                event.time,
                event.container.name,
                event.id_route,
                event.num_arrivals,
                event.volume,
            )
            for event in self.buffer
            if isinstance(event, ServiceEvent)
        ]

        self.write.executemany(
            """-- sql
                INSERT INTO service_events (
                    time,
                    container,
                    id_route,
                    num_arrivals,
                    volume
                ) VALUES (?, ?, ?, ?, ?)
            """,
            services,
        )

        self.write.commit()
        self.buffer = []

    def __del__(self):
        if self.buffer:
            self._commit()

        self.read.close()
        self.write.close()


def _containers2loc(con: sqlite3.Connection, containers: list[Container]):
    names = ", ".join(f"'{c.name}'" for c in containers)
    sql = f"""-- sql
        SELECT id_location
        FROM containers
        WHERE name in ({names})
        ORDER BY id_location;
    """
    return [id_location for id_location, in con.execute(sql)]
