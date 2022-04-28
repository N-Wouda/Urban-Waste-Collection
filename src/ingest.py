from pathlib import Path


def main():
    # Remove existing database, if any - ingest starts from scratch.
    db = Path("data/waste.db")
    db.unlink(missing_ok=True)

    # Set-up database connection and table structure.
    # TODO

    # Import data from raw Excel files.
    # TODO


if __name__ == "__main__":
    main()
