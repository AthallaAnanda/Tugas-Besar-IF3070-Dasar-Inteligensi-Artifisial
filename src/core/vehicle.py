"""Cerita soal kendaraan yang mau kita muat ke kapal.

Isinya data dasar kendaraan, contohnya identitas, ukuran,
kapasitas, sama nilai ShippingFee nya. Datanya nanti
disesuaikan lagi sama spek tubes dan file data aslinya.
"""

from dataclasses import dataclass


@dataclass
class Vehicle:
    """Info statis satu kendaraan, dibaca dari data input."""

    id: str
    width: float
    length: float
    capacity: float = 0.0
    shipping_fee: float = 0.0

    # TODO Tahap 1 Anggota 1, tolong sesuaikan field ini sama spek tubes dan data aslinya ya
