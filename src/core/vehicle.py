"""Data kendaraan yang tersedia untuk dimuat ke kapal"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Vehicle:
    """Ukuran disini memakai satuan sel grid, sedangkan berat memakai satuan kapasitas kapal"""

    id: str
    width: int
    length: int
    shipping_fee: float
    weight: float
    eta: int

    def __post_init__(self):
        if not self.id or type(self.width) is not int or type(self.length) is not int:
            raise ValueError("Identitas dan ukuran kendaraan harus valid")
        if self.width <= 0 or self.length <= 0:
            raise ValueError("Ukuran kendaraan harus positif")
        if self.weight < 0 or self.shipping_fee < 0 or type(self.eta) is not int or self.eta < 0:
            raise ValueError("Berat, tarif, dan ETA kendaraan tidak boleh negatif")
