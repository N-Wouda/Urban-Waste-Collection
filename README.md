# Groningen waste collection

[![CI](https://github.com/N-Wouda/Groningen-Waste-Collection/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/N-Wouda/Groningen-Waste-Collection/actions/workflows/CI.yml)

This repository hosts code investigating how to improve waste collection in the Municipality of Groningen.
The code includes:

- Scripts for ingesting raw data files into an SQL database;
- A simulation environment simulating waste arrivals at underground container clusters;
- Forecasting and vehicle routing techniques to plan waste collection;
- Analysis tools for evaluating different planning techniques.

Additionally, the notebooks in `notebooks/` reproduce the results from our paper.
This includes the results from the case study (in `case_study.ipynb`), and an exploratory analysis of the case study setting and sensor data (in `exploration.ipynb` and `sensors.ipynb`, respectively).

## Installation

Update or get `poetry`, and then simply use `poetry install` from the repository root.

## Programs

The following programs are currently available:

- `ingest`, the ingestion script.
  This script ingests raw data files into an SQL database.
- `matrix`, the distance and duration matrix calculation script.
  This relies on OSRM; see the `osrm/` directory for details.
- `simulate`, the simulation runscript.
  This script runs a single simulation using a given collection strategy.
  It assumes the data has been set up correctly using the `ingest` and `matrix` scripts.
- `analyze`, the analysis script.
  This script analyses the output of the `simulate` script.
- `plot`, which can plot a set of simulated routes on top of OSM.

These programs can be ran as `poetry run <script name>`, for example:
```shell
poetry run ingest
```

You may pass the `--help` option to learn more about program usage.
Some programs depend on data available in a `data/` directory.
This data is not made available via the GitHub repository.

## How to cite

TODO pre-print details

## License

Copyright (C) since 2023, Niels Wouda and Nicky van Foreest

Unless expressly noted otherwise, the code in this repository is free software:
you can redistribute it and/or modify it under the terms of the GNU Affero
General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

The code in this repository is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
for more details.

You should have received a copy of the GNU Affero General Public License as
part of this repository. If not, see <https://www.gnu.org/licenses/>.
