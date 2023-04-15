import sqlite3
from typing import Any, Callable

from .avg_fill_factor import avg_fill_factor
from .avg_service_level import avg_service_level
from .num_arrivals_per_hour import num_arrivals_per_hour

Measure = Callable[[sqlite3.Connection], Any]

MEASURES: dict[str, Measure] = {
    "Avg. fill factor": avg_fill_factor,
    "Avg. service level": avg_service_level,
    "Number of arrivals per hour": num_arrivals_per_hour,
}
