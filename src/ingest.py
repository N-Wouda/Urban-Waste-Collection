from pathlib import Path


def main():
    db = Path("data/waste.db")
    db.unlink(missing_ok=True)

    # TODO


if __name__ == "__main__":
    main()
