from __future__ import annotations

import math
import sqlite3
from functools import cache
from typing import Any, Optional

import numpy as np

from waste.constants import BUFFER_SIZE, HOURS_IN_DAY, ID_DEPOT
from waste.enums import LocationType
from waste.measures import Measure

from .Container import Container
from .Depot import Depot
from .Event import ArrivalEvent, Event, ServiceEvent
from .Route import Route
from .Vehicle import Vehicle


class Database:
    """
    Simple database wrapper/model class for interacting with the static and
    simulation data.
    """

    def __init__(self, src_db: str, res_db: str):
        self.buffer: list[ArrivalEvent | ServiceEvent] = []

        self.read = sqlite3.connect(src_db)
        self.write = sqlite3.connect(res_db)

        # Prepare the result database
        self.write.execute("ATTACH DATABASE ? AS source;", (src_db,))
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
                    vehicle VARCHAR,
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

        return [
            Container(name, rates[name], capacity)
            for name, capacity in capacities.items()
        ]

    @cache
    def depot(self) -> Depot:
        sql = "SELECT name FROM locations WHERE type = ?;"
        rows = [d for d in self.read.execute(sql, (LocationType.DEPOT,))]
        assert len(rows) == 1  # there should be only a single depot!
        return Depot(*rows[0])

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
        id_locations = [ID_DEPOT] + id_containers
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
        id_locations = [ID_DEPOT] + id_containers
        return durations[np.ix_(id_locations, id_locations)]

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
        # Only arrival and service events are logged; other events are
        # currently an intended no-op.
        if isinstance(item, (ArrivalEvent, ServiceEvent)):
            self.buffer.append(item)

            if len(self.buffer) >= BUFFER_SIZE:
                self._commit()
        elif isinstance(item, Route):
            sql = "INSERT INTO routes (vehicle) VALUES (?)"
            cursor = self.write.execute(sql, (item.vehicle.name,))
            self.write.commit()
            return cursor.lastrowid

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
                event.vehicle.name,
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
                    vehicle,
                    num_arrivals,
                    volume
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            services,
        )

        self.write.commit()
        self.buffer = []

    def __del__(self):
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
