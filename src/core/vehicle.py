
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Vehicle:

    id: str
    width: int
    length: int
    shipping_fee: float
    weight: float
    eta: int

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Identitas kendaraan harus berupa teks yang tidak kosong")
        if type(self.width) is not int or type(self.length) is not int:
            raise ValueError("Ukuran kendaraan harus bilangan bulat")
        if self.width <= 0 or self.length <= 0:
            raise ValueError("Ukuran kendaraan harus positif")
        if any(type(value) not in (int, float) or not isfinite(value) or value < 0
               for value in (self.weight, self.shipping_fee)):
            raise ValueError("Berat dan tarif kendaraan harus bilangan tidak negatif yang terbatas")
        if type(self.eta) is not int or self.eta < 0:
            raise ValueError("ETA kendaraan harus bilangan bulat tidak negatif")
