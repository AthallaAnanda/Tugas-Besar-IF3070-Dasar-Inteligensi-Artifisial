
from dataclasses import dataclass, field
from math import isfinite

from .placement import Placement


@dataclass(frozen=True)
class Ship:

    id: str
    width: int
    length: int
    max_capacity: float

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Identitas kapal harus berupa teks yang tidak kosong")
        if type(self.width) is not int or type(self.length) is not int:
            raise ValueError("Ukuran kapal harus bilangan bulat")
        if self.width <= 0 or self.length <= 0:
            raise ValueError("Ukuran kapal harus positif")
        if (type(self.max_capacity) not in (int, float)
                or not isfinite(self.max_capacity) or self.max_capacity < 0):
            raise ValueError("Kapasitas kapal harus bilangan tidak negatif yang terbatas")


@dataclass
class ShipState:

    ship: Ship
    placements: list[Placement] = field(default_factory=list)
