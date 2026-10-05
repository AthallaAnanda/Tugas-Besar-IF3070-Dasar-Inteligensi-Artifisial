"""Posisi dan orientasi kendaraan yang berada di geladak"""

from dataclasses import dataclass

from .vehicle import Vehicle


@dataclass(frozen=True)
class Placement:
    """Koordinat x dan y menunjuk sel kiri atas kendaraan pada grid"""

    vehicle_id: str
    ship_id: str
    x: int
    y: int
    orientation: str = "horizontal"

    def __post_init__(self):
        if not self.vehicle_id or not self.ship_id:
            raise ValueError("Identitas kendaraan dan kapal harus diisi")
        if type(self.x) is not int or type(self.y) is not int:
            raise ValueError("Koordinat harus bilangan bulat")
        if self.orientation not in ("horizontal", "vertical"):
            raise ValueError("Orientasi harus horizontal atau vertical")

    def occupied_size(self, vehicle_width: int, vehicle_length: int):
        """Ukuran berubah ketika kendaraan diputar menjadi vertical"""
        if self.orientation == "vertical":
            return vehicle_length, vehicle_width
        return vehicle_width, vehicle_length

    def occupied_cells(self, vehicle: Vehicle):
        """Daftar koordinat sel yang ditutupi kendaraan, termasuk di luar geladak"""
        width, length = self.occupied_size(vehicle.width, vehicle.length)
        return {(x, y) for x in range(self.x, self.x + width)
                for y in range(self.y, self.y + length)}
