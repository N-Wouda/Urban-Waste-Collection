# OSRM

We use [OSRM](https://github.com/Project-OSRM/osrm-backend) to compute distances.
A custom "truck" profile is used to simulate garbage trucks.

OSRM can be set-up using Docker.
It can be ran with the latest OSM map data for Groningen, which can be downloaded [here](http://download.geofabrik.de/europe/netherlands/groningen.html) and should be placed into `osrm/data`.
In this working directory, I run the Docker instance using `run.bat`.

Once the Docker instance is running with the Groningen data, the `distance` program can be used from the project's root to determine distances and durations.
