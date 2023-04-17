@echo off 

SET curdir="%cd%"
set where=/data/groningen-latest
set mounts=-v "%curdir%/data:/data" -v "%curdir%/profiles/car.lua:/opt/car.lua" -v "%curdir%/profiles/way_handlers.lua:/opt/lib/way_handlers.lua"

:: Redo preparation work because the profile could have changed. It's pretty fast on most machines,
:: so there's no great pain in doing this every time.
docker run -t %mounts% ghcr.io/project-osrm/osrm-backend osrm-extract -p /opt/car.lua %where%.osm.pbf
docker run -t %mounts% ghcr.io/project-osrm/osrm-backend osrm-partition %where%.osrm
docker run -t %mounts% ghcr.io/project-osrm/osrm-backend osrm-customize %where%.osrm

:: Runs the actual OSRM backend on port 5000.
docker run -t -i -p 5000:5000 -v "%curdir%/data:/data" ghcr.io/project-osrm/osrm-backend osrm-routed --algorithm mld %where%.osrm
