# OSRM

We use [OSRM](https://github.com/Project-OSRM/osrm-backend) to compute distances.
A custom "truck" profile is used to simulate garbage trucks.

OSRM can be set-up using Docker, see the instructions on the linked page.
It can be ran with the latest OSM map data for Groningen, which can be downloaded [here](http://download.geofabrik.de/europe/netherlands/groningen.html).
Once the Docker instance is running with the Groningen data, the `distance` program can be used from the project's root to determine distances and durations.

In this working directory, I do the following to run OSRM using Docker:
```shell
docker run -t -i -p 5000:5000 -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend osrm-routed --algorithm mld /data/groningen-latest.osrm
```
