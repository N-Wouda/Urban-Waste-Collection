from typing import Any, Callable

from waste.classes import Database

from .avg_excess_volume import avg_excess_volume as avg_excess_volume
from .avg_fill_factor import avg_fill_factor as avg_fill_factor
from .avg_num_arrivals_between_service import (
    avg_num_arrivals_between_service as avg_num_arrivals_between_service,
)
from .avg_num_routes_per_day import (
    avg_num_routes_per_day as avg_num_routes_per_day,
)
from .avg_route_distance import avg_route_distance as avg_route_distance
from .avg_route_duration import avg_route_duration as avg_route_duration
from .avg_route_stops import avg_route_stops as avg_route_stops
from .avg_service_level import avg_service_level as avg_service_level
from .num_arrivals import num_arrivals as num_arrivals
from .num_arrivals_per_hour import (
    num_arrivals_per_hour as num_arrivals_per_hour,
)
from .num_services import num_services as num_services
from .num_unserved_containers import num_unserved_containers

Measure = Callable[[Database], Any]

MEASURES: list[Measure] = [
    avg_excess_volume,
    avg_fill_factor,
    avg_num_arrivals_between_service,
    avg_num_routes_per_day,
    avg_route_distance,
    avg_route_duration,
    avg_route_stops,
    avg_service_level,
    num_arrivals_per_hour,
    num_arrivals,
    num_services,
    num_unserved_containers,
]
