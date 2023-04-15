class Vehicle:
    def __init__(self, name: str, capacity: float):
        self.name = name
        self.capacity = capacity

    def __str__(self) -> str:
        return f"Vehicle(name={self.name}, capacity={self.capacity:.2f})"

    # TODO
