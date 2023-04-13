# Groningen waste collection

This repository hosts code we use to improve waste collection in/by the Municipality of Groningen from underground containers.
The code includes:

- Scripts for ingesting raw data files into an SQL database;
- A simulation environment simulating waste arrivals;
- Forecasting and vehicle routing techniques to plan waste collection.

## Installation

Update or get `poetry`, and then simply use `poetry install` from the repository root.
Scripts can be ran as `poetry run <script name>`, for example:
```
poetry run ingest
```
will run the `waste/ingest.py` script.

> *Note* that most programs depend on data available in the `data/` directory.
> This directory is not on GitHub.
