from dataclasses import dataclass, field

import tomli


@dataclass
class Configuration:
    volume_range: tuple[float, float] = (30, 65)
    shift_plan: list[float] = field(default_factory=lambda: [6, 12])

    @classmethod
    def from_file(cls, where: str):
        with open(where, "rb") as fh:
            params = tomli.load(fh)

        return cls(**params)
