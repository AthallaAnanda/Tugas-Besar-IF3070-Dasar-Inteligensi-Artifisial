"""Ukuran kapal dan kendaraan yang sedang menempati geladaknya."""

from dataclasses import dataclass, field

from .placement import Placement


@dataclass(frozen=True)
class Ship:
    """Kapasitas merupakan batas jumlah berat kendaraan yang diangkut"""

    id: str
    width: int
    length: int
    max_capacity: float

    def __post_init__(self):
        if not self.id or type(self.width) is not int or type(self.length) is not int:
            raise ValueError("Identitas dan ukuran kapal harus valid")
        if self.width <= 0 or self.length <= 0 or self.max_capacity < 0:
            raise ValueError("Ukuran kapal harus positif dan kapasitas tidak boleh negatif")


@dataclass
class ShipState:
    """Penempatan kendaraan pada satu kapal dalam sebuah solusi"""

    ship: Ship
    placements: list[Placement] = field(default_factory=list)
