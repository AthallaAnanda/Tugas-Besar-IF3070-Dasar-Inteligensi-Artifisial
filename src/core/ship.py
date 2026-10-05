"""Cerita soal kapal dan geladaknya.

Di sini kita nyimpen ukuran kapal, kapasitasnya, plus kondisi
geladak waktu sudah diisi kendaraan. Satu objek ShipState itu
gambaran satu kapal di dalam satu solusi.
"""

from dataclasses import dataclass, field


@dataclass
class Ship:
    """Info statis kapal. Sederhananya ya cuma identitas dan ukuran dulu."""

    id: str = "ship_1"
    width: float = 0.0
    length: float = 0.0
    capacity: float = 0.0

    # TODO Tahap 1 Anggota 1, nanti tambah grid sama daftar placement di sini ya


@dataclass
class ShipState:
    """Kondisi satu kapal di dalam sebuah State. Ini yang bikin multi ship jadi gampang."""

    ship: Ship
    placements: list = field(default_factory=list)

    # TODO Tahap 1 Anggota 1, nanti bikin helper buat cek grid yang kepakai
