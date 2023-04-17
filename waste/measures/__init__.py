import sqlite3
from typing import Any, Callable

from .avg_fill_factor import avg_fill_factor
from .avg_num_arrivals_between_service import avg_num_arrivals_between_service
from .avg_route_stops import avg_route_stops
from .avg_service_level import avg_service_level
from .num_arrivals import num_arrivals
from .num_arrivals_per_hour import num_arrivals_per_hour
from .num_services import num_services

Measure = Callable[[sqlite3.Connection], Any]

MEASURES: dict[str, Measure] = {
    "Avg. number of inter-service arrivals": avg_num_arrivals_between_service,
    "Avg. number of route stops": avg_route_stops,
    "Avg. fill factor": avg_fill_factor,
    "Avg. service level": avg_service_level,
    "Number of arrivals per hour": num_arrivals_per_hour,
    "Number of arrivals": num_arrivals,
    "Number of services": num_services,
}
