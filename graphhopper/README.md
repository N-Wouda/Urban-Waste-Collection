# GraphHopper

We use [GraphHopper](https://github.com/graphhopper/graphhopper) to compute distances.
A customer "truck" profile is used to simulate garbage trucks.

GraphHopper can be obtained as a standalone Java application.
It can be ran with the latest OSM map data for Groningen, which can be downloaded [here](http://download.geofabrik.de/europe/netherlands/groningen.html).
To use GraphHopper, place the `graphhopper.jar` and `groningen-latest.osm.pbf` files in this directory.
Then run
```shell
    java -D"dw.graphhopper.datareader.file=groningen-latest.osm.pbf" -jar .\graphhopper-web-7.0.jar server config.yml
```
