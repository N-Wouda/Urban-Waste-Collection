from waste.enums import LocationType

# Stadsbeheer; the junkyard is ~200m down the road from this location.
# NOTE: this value exists here for ingesting in the ingest script. Use the
# depot() method on the Database to get the actual data you need!
DEPOT = (
    "Depot",  # name
    "Duinkerkenstraat 45",  # description
    53.197625,  # latitude
    6.6127883,  # longitude
    LocationType.DEPOT,
)

BUFFER_SIZE = 999
HOURS_IN_DAY = 24
