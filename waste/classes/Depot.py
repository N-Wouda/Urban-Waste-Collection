class Depot:
    def __init__(self, name: str, location: tuple[float, float]):
        self.name = name
        self.location = location  # (lat, lon) pair

    def __str__(self) -> str:
        return f"Depot(name={self.name})"
