from typing import Any, Callable

from waste.classes import Database

from .avg_fill_factor import avg_fill_factor
from .avg_num_arrivals_between_service import avg_num_arrivals_between_service
from .avg_route_distance import avg_route_distance
from .avg_route_stops import avg_route_stops
from .avg_service_level import avg_service_level
from .num_arrivals import num_arrivals
from .num_arrivals_per_hour import num_arrivals_per_hour
from .num_services import num_services

Measure = Callable[[Database], Any]

MEASURES: list[Measure] = [
    avg_num_arrivals_between_service,
    avg_route_distance,
    avg_route_stops,
    avg_fill_factor,
    avg_service_level,
    num_arrivals_per_hour,
    num_arrivals,
    num_services,
]
