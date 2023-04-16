import sqlite3
from typing import Any

import numpy as np

from waste.constants import BUFFER_SIZE, HOURS_IN_DAY
from waste.measures import Measure

from .Container import Container
from .Event import Event, EventType
from .Vehicle import Vehicle


class Database:
    """
    Simple database wrapper/model class for interacting with the static and
    simulation data.
    """

    def __init__(self, src_db: str, res_db: str):
        self.buffer: list[Event] = []

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

                CREATE TABLE service_events (
                    time FLOAT,
                    container VARCHAR,
                    vehicle VARCHAR,
                    num_arrivals INT,
                    volume FLOAT
                );
            """
        )

    def containers(self) -> list[Container]:
        sql = """-- sql
            SELECT cr.container,
                   c.capacity,
                   cr.hour,
                   cr.rate
            FROM container_rates AS cr
                    INNER JOIN containers AS c
                                ON c.container = cr.container
            ORDER BY cr.container, cr.hour;
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

    def vehicles(self) -> list[Vehicle]:
        sql = "SELECT vehicle, capacity FROM vehicles;"
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

    def store(self, event: Event):
        self.buffer.append(event)

        if len(self.buffer) >= BUFFER_SIZE:
            self._commit()

    def _commit(self):
        self.write.execute("BEGIN TRANSACTION;")

        arrivals = [
            (
                event.time,
                event.kwargs["container"].name,
                event.kwargs["volume"],
            )
            for event in self.buffer
            if event.type == EventType.ARRIVAL
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
                event.kwargs["container"].name,
                event.kwargs["vehicle"].name,
                event.kwargs["container"].num_arrivals,
                event.kwargs["container"].volume,
            )
            for event in self.buffer
            if event.type == EventType.SERVICE
        ]

        self.write.executemany(
            """-- sql
                INSERT INTO service_events (
                    time,
                    container,
                    vehicle,
                    num_arrivals,
                    volume
                ) VALUES (?, ?, ?, ?, ?)
            """,
            services,
        )

        self.write.commit()
        self.buffer = []

    def __del__(self):
        self.read.close()
        self.write.close()
