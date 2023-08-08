# Groningen waste collection

[![CI](https://github.com/N-Wouda/Groningen-Waste-Collection/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/N-Wouda/Groningen-Waste-Collection/actions/workflows/CI.yml)

This repository hosts code we use to improve waste collection in/by the Municipality of Groningen from underground containers.
The code includes:

- Scripts for ingesting raw data files into an SQL database;
- A simulation environment simulating waste arrivals;
- Forecasting and vehicle routing techniques to plan waste collection.

## Installation

Update or get `poetry`, and then simply use `poetry install` from the repository root.

## Programs

The following programs are currently available:

- `distance`, the distance and duration matrix calculation script.
  This relies on OSRM; see the `osrm/` directory for details.
- `ingest`, the ingestion script.
  This script ingests raw data files into an SQL database.
- `simulate`, the simulation runscript.
  This script runs a single simulation using a given collection strategy.
- `analyze`, the analysis script.

These programs can be ran as `poetry run <script name>`, for example:
```shell
poetry run ingest
```

Note that most programs depend on data available in the `data/` directory.
This directory is not on GitHub.
