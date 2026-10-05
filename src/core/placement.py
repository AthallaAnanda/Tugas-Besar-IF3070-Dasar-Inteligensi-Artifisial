"""Cerita soal penempatan satu kendaraan di atas geladak.

Intinya kita catat kendaraan apa, taruh di kapal mana,
koordinatnya di mana, sama posisinya tidur atau berdiri.
"""

from dataclasses import dataclass


@dataclass
class Placement:
    """Satu titik penempatan kendaraan di satu kapal."""

    vehicle_id: str
    ship_id: str = "ship_1"
    x: float = 0.0
    y: float = 0.0
    orientation: str = "horizontal"  # isinya horizontal atau vertical

    def occupied_size(self, vehicle_width: float, vehicle_length: float):
        """Hitung ukuran kepakai setelah orientasi dipasang. Kalau vertical ya ditukar saja."""
        # TODO Tahap 1 Anggota 1, lengkapi logika putar ukuran di sini
        if self.orientation == "vertical":
            return (vehicle_length, vehicle_width)
        return (vehicle_width, vehicle_length)

    # TODO Tahap 1 Anggota 1, bikin helper occupied_cells buat petak grid yang kepakai
