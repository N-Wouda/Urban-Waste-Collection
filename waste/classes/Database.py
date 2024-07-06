from __future__ import annotations

import logging
import math
import sqlite3
from datetime import datetime, time
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from waste.constants import BUFFER_SIZE, HOURS_IN_DAY
from waste.enums import LocationType

from .Cluster import Cluster
from .Depot import Depot
from .Event import (
    ArrivalEvent,
    BreakEvent,
    Event,
    ServiceEvent,
    ShiftPlanEvent,
)
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
        self.buffer: list[Event] = []
        self.read = sqlite3.connect(src_db)

        # Prepare the result database
        res_db_exists = Path(res_db).exists()
        self.write = sqlite3.connect(res_db)
        self.write.execute("ATTACH DATABASE ? AS source;", (src_db,))

        if not res_db_exists:
            self.write.executescript(
                """-- sql
                    CREATE TABLE routes (
                        id_route INTEGER PRIMARY KEY,
                        vehicle NAME,
                        start_time DATETIME
                    );

                    CREATE TABLE arrival_events (
                        time DATETIME,
                        cluster VARCHAR,
                        volume FLOAT
                    );

                    CREATE TABLE break_events (
                        time DATETIME,
                        duration FLOAT,
                        id_route INTEGER references routes
                    );

                    CREATE TABLE service_events (
                        time DATETIME,
                        duration FLOAT,
                        cluster VARCHAR,
                        id_route INTEGER references routes,
                        num_arrivals INT,
                        volume FLOAT
                    );
                """
            )

    @cache
    def clusters(self) -> list[Cluster]:
        def rates(name: str) -> list[float]:
            sql = """-- sql
                SELECT hour, rate
                FROM cluster_rates
                WHERE cluster = ?
                ORDER BY hour;  -- must order by ID, not name!
            """
            res = [0.0] * HOURS_IN_DAY
            for hour, rate in self.read.execute(sql, [name]):
                res[hour] = rate
            return res

        sql = """-- sql
            SELECT c.name,
                   c.id_location,
                   c.num_containers,
                   c.tw_late,
                   c.capacity,
                   c.correction_factor,
                   l.latitude,
                   l.longitude
            FROM clusters AS c
                INNER JOIN locations AS l
                    ON c.id_location = l.id_location;
        """
        rows = self.read.execute(sql)

        return [
            Cluster(
                name,
                id_location,
                rates(name),
                capacity,
                (lat, lon),
                time.fromisoformat(tw_late),
                num_containers,
                corr_factor,
            )
            for (
                name,
                id_location,
                num_containers,
                tw_late,
                capacity,
                corr_factor,
                lat,
                lon,
            ) in rows
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
        index 0) and all clusters returned by ``clusters()``, in order.
        The distance matrix is *not* symmetric.
        """
        cursor = self.read.execute("SELECT distance FROM matrix;")
        data = np.array([distance for distance in cursor])
        size = math.isqrt(len(data))
        distances = np.array(data).reshape((size, size))

        id_locations = [0] + [c.id_location for c in self.clusters()]
        return distances[np.ix_(id_locations, id_locations)]

    @cache
    def durations(self) -> np.array:
        """
        Returns the matrix of travel durations (in seconds) for the depot (at
        index 0) and all clusters returned by ``clusters()``, in order.
        The duration matrix is *not* symmetric.
        """
        cursor = self.read.execute("SELECT duration FROM matrix;")
        data = np.array([duration for duration in cursor])
        size = math.isqrt(len(data))
        durations = np.array(data).reshape((size, size))

        id_locations = [0] + [c.id_location for c in self.clusters()]
        mat = durations[np.ix_(id_locations, id_locations)]
        return mat.astype(np.timedelta64(1, "s"))

    @cache
    def vehicles(self) -> list[Vehicle]:
        sql = "SELECT name, capacity FROM vehicles;"
        return [
            Vehicle(name, capacity)
            for name, capacity in self.read.execute(sql)
        ]

    def compute(self, measure: Measure, after: datetime = datetime.min) -> Any:
        """
        Computes the given performance measure from data managed by this
        database, using data collected after the given datetime.
        """
        self.commit()
        return measure(self, after)

    def store(self, item: Event | Route) -> Optional[int]:
        # Only arrival, service and route events are logged; other arguments
        #  are currently an intended no-op.
        match item:
            case Event():
                assert item.is_sealed()

                self.buffer.append(item)
                if len(self.buffer) >= BUFFER_SIZE:
                    self.commit()

                return None
            case Route(vehicle=vehicle, start_time=start_time):
                sql = "INSERT INTO routes (vehicle, start_time) VALUES (?, ?)"
                cursor = self.write.execute(sql, (vehicle.name, start_time))
                self.write.commit()
                return cursor.lastrowid
            case _:
                return None

    def commit(self):
        """
        Commits any events in the write buffer to the write connection. After
        calling this method, the write buffer is empty and all events have been
        written to the write connection's database.
        """
        self.write.execute("BEGIN TRANSACTION;")

        for event in self.buffer:
            match event:
                case ArrivalEvent() as e:
                    self.write.execute(
                        """--sql
                            INSERT INTO arrival_events (
                                time,
                                cluster,
                                volume
                            ) VALUES (?, ?, ?);
                        """,
                        (e.time, e.cluster.name, e.volume),
                    )
                case ServiceEvent() as e:
                    self.write.execute(
                        """--sql
                            INSERT INTO service_events (
                                time,
                                duration,
                                cluster,
                                id_route,
                                num_arrivals,
                                volume
                            ) VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        (
                            e.time,
                            e.duration.total_seconds(),
                            e.cluster.name,
                            e.id_route,
                            e.num_arrivals,
                            e.volume,
                        ),
                    )
                case BreakEvent() as e:
                    self.write.execute(
                        """--sql
                            INSERT INTO break_events (
                                time,
                                duration,
                                id_route
                            ) VALUES (?, ?, ?);
                        """,
                        (
                            e.time,
                            e.duration.total_seconds(),
                            e.id_route,
                        ),
                    )
                case ShiftPlanEvent():
                    continue
                case _:
                    msg = f"Event of type {type(event)} not understood."
                    logger.error(msg)
                    raise TypeError(msg)

        self.write.commit()
        self.buffer = []

    def __del__(self):
        if self.buffer:
            self.commit()

        self.read.close()
        self.write.close()
